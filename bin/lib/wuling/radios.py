"""Page-scoped public radio snapshots and bounded, private native actions."""

import ipaddress
import json
import os
import re
import signal
import shutil
import subprocess
import sys
import time
import uuid
from urllib.parse import urlsplit
from . import Error
from . import devices, status

NM = "org.freedesktop.NetworkManager"
NM_PATH = "/org/freedesktop/NetworkManager"
BLUEZ = "org.bluez"


def unbox(value):
    if isinstance(value, dict):
        if set(value) == {"type", "data"}:
            return unbox(value["data"])
        return {key: unbox(item) for key, item in value.items()}
    return [unbox(item) for item in value] if isinstance(value, list) else value


def nmprops(path, interface):
    return unbox(devices.properties("system", NM, path, interface))


def nmcall(path, interface, method):
    result = devices.call("system", NM, path, interface, method)
    return unbox(result[0]) if result else []


def rfkill(kind):
    return [status.text(path / "soft").strip() == "1"
            for path in (status.SYS / "class/rfkill").glob("rfkill*")
            if status.text(path / "type").strip() == kind]


def bluetooth_present():
    return bool(rfkill("bluetooth")) or any((status.SYS / "class/bluetooth").glob("hci*"))


def ssid(value):
    try:
        return bytes(value).decode("utf-8", errors="replace")
    except (TypeError, ValueError):
        return ""


def bssid_matches(value, address):
    if not value:
        return True
    # NetworkManager's settings API uses a byte array for a profile's BSSID;
    # AccessPoint.HwAddress is the printable form of the same address.
    if isinstance(value, list):
        if len(value) != 6 or any(type(byte) is not int or not 0 <= byte <= 255 for byte in value):
            return False
        value = ":".join(f"{byte:02X}" for byte in value)
    return str(value).upper() == str(address).upper()


def wifi_device():
    root = nmprops(NM_PATH, NM)
    choices = []
    for path in root.get("Devices", [])[:32]:
        data = nmprops(path, NM + ".Device")
        if data.get("DeviceType") == 2 and data.get("Managed") is True:
            choices.append((path, data))
    path, device = next((row for row in choices if row[1].get("State") == 100), choices[0] if choices else ("", {}))
    return {"present": bool(choices) or bool(rfkill("wlan")), "enabled": root.get("WirelessEnabled") is True,
            "hardware_enabled": root.get("WirelessHardwareEnabled") is True,
            "interface": device.get("Interface", ""), "device": path}, device


class Wifi:
    def __init__(self):
        self.initial, _ = wifi_device()

    def read(self):
        result, device = wifi_device()
        result.update(networks=[], linked=None, age=None)
        if not result["device"]:
            return result
        wireless = nmprops(result["device"], NM + ".Device.Wireless")
        scan = wireless.get("LastScan", -1)
        result["age"] = max(0, int(time.clock_gettime(time.CLOCK_BOOTTIME) - scan / 1000)) if scan >= 0 else None
        # GetSettings contains public connection settings, never GetSecrets.
        profiles = []
        for path in nmcall(NM_PATH + "/Settings", NM + ".Settings", "ListConnections")[:128]:
            settings = nmcall(path, NM + ".Settings.Connection", "GetSettings")
            if isinstance(settings, dict) and settings.get("connection", {}).get("type") == "802-11-wireless":
                profiles.append(settings)
        for path in wireless.get("AccessPoints", [])[:256]:
            ap = nmprops(path, NM + ".AccessPoint")
            name = ssid(ap.get("Ssid", []))
            if not name:
                continue
            flags = ap.get("WpaFlags", 0) | ap.get("RsnFlags", 0)
            security = "enterprise" if flags & 0x2200 else "sae" if flags & 0x400 else "psk" if flags & 0x100 else "owe" if flags & 0x1800 else "wep" if ap.get("Flags", 0) & 1 else "open"
            matching = [entry for entry in profiles if entry.get("802-11-wireless", {}).get("ssid", []) == ap.get("Ssid")
                        and entry.get("connection", {}).get("interface-name", result["interface"]) == result["interface"]
                        and bssid_matches(entry.get("802-11-wireless", {}).get("bssid"), ap.get("HwAddress", ""))
                        and entry.get("802-11-wireless-security", {}).get("key-mgmt", "open") in
                        ({"psk": ("wpa-psk",), "sae": ("sae", "wpa-psk"), "enterprise": ("wpa-eap", "ieee8021x"), "wep": ("none",), "owe": ("owe",)}.get(security, ("open",)))]
            matching.sort(key=lambda entry: entry["connection"].get("timestamp", 0), reverse=True)
            frequency = ap.get("Frequency", 0)
            row = {"id": path, "name": status.label(name, 64), "address": ap.get("HwAddress", ""), "security": security, "_ssid": tuple(ap.get("Ssid", [])),
                   "signal": ap.get("Strength", 0), "band": "6G" if frequency >= 5925 else "5G" if frequency >= 4900 else "2.4G",
                   "uuid": matching[0]["connection"].get("uuid", "") if matching else "",
                   "connected": device.get("State") == 100 and wireless.get("ActiveAccessPoint") == path}
            if row["connected"]:
                active = nmprops(device.get("ActiveConnection", "/"), NM + ".Connection.Active")
                row["uuid"] = active.get("Uuid", row["uuid"])
                ip = nmprops(device.get("Ip4Config", "/"), NM + ".IP4Config")
                addresses = ip.get("AddressData", [])
                row.update(ipv4=addresses[0].get("address", "") if addresses else "", gateway=ip.get("Gateway", ""),
                           rate=wireless.get("Bitrate", 0) / 1000, tailnet=tailnet_uses(result["interface"]))
                result["linked"] = row
            else:
                result["networks"].append(row)
        # One row per SSID/security/band, retaining the strongest access point.
        unique = {}
        for row in sorted(result["networks"], key=lambda row: -row["signal"]):
            unique.setdefault((row["_ssid"], row["security"], row["band"]), row)
        result["networks"] = list(unique.values())
        for row in result["networks"] + ([result["linked"]] if result["linked"] else []):
            row.pop("_ssid", None)
        return result


def tailnet_uses(interface):
    data = status.probe_json(["tailscale", "status", "--json"])
    if data.get("BackendState") != "Running":
        return False
    # Only prove direct live transports. A default route alone cannot prove
    # which interface the daemon used for a relayed connection.
    for peer in list(data.get("Peer", {}).values())[:128]:
        address = peer.get("CurAddr", "")
        if not peer.get("Active") or not address:
            continue
        try:
            host = address.rsplit(":", 1)[0].strip("[]")
            ipaddress.ip_address(host)
            route = json.loads(status.probe(["ip", "-j", "route", "get", host]) or "[]")
            if any(row.get("dev") == interface for row in route):
                return True
        except (ValueError, TypeError):
            pass
    return False


def bluetooth():
    values = devices.call("system", BLUEZ, "/", "org.freedesktop.DBus.ObjectManager", "GetManagedObjects")
    objects = unbox(values[0]) if values and isinstance(values[0], dict) else {}
    adapters = {path: interfaces[BLUEZ + ".Adapter1"] for path, interfaces in objects.items() if BLUEZ + ".Adapter1" in interfaces}
    default = status.probe(["bluetoothctl", "show"], timeout=2) or ""
    address = re.search(r"^Controller ([0-9A-Fa-f:]{17})\b", default)
    path = next((path for path, data in adapters.items() if address and data.get("Address") == address[1]), "")
    adapter = adapters.get(path, {})
    rows = []
    for device, interfaces in objects.items():
        data = interfaces.get(BLUEZ + ".Device1", {})
        if not path or data.get("Adapter") != path:
            continue
        icon = str(data.get("Icon", ""))
        rows.append({"id": device, "address": data.get("Address", ""), "name": status.label(data.get("Alias") or data.get("Name") or data.get("Address")),
                     "icon": "headphones" if "audio" in icon else "keyboard" if "keyboard" in icon else "mouse" if "mouse" in icon else "smartphone" if "phone" in icon else "bluetooth",
                     "connected": data.get("Connected") is True, "paired": data.get("Paired") is True,
                     "battery": status.number(interfaces.get(BLUEZ + ".Battery1", {}).get("Percentage"), high=100)})
    rows.sort(key=lambda row: (not row["connected"], not row["paired"], row["name"].casefold()))
    return {"present": bool(adapters) or bluetooth_present(), "enabled": any(data.get("Powered") for data in adapters.values()),
            "adapter": path, "name": status.label(adapter.get("Alias", "")), "discovering": adapter.get("Discovering") is True, "devices": rows}


def tailnet():
    if not shutil.which("tailscale"):
        return {"present": False}
    data = status.probe_json(["tailscale", "status", "--json"])
    own = data.get("Self") or {}
    peers = []
    for peer in list((data.get("Peer") or {}).values())[:512]:
        peers.append({"name": status.label(peer.get("HostName") or peer.get("DNSName", "").split(".")[0]),
                      "online": peer.get("Online") is True,
                      "route": "direct" if peer.get("CurAddr") else "relay" if peer.get("Relay") else ""})
    peers.sort(key=lambda row: (not row["online"], row["name"].casefold()))
    exit_id = (data.get("ExitNodeStatus") or {}).get("ID")
    exit_node = next((peer for peer in (data.get("Peer") or {}).values() if exit_id and peer.get("ID") == exit_id), {})
    return {"present": True, "state": data.get("BackendState", "Unavailable"), "name": status.label(own.get("HostName")),
            "address": next(iter(own.get("TailscaleIPs") or []), ""), "exit_node": status.label(exit_node.get("HostName")),
            "online": sum(row["online"] for row in peers), "peers": peers}


def execute(argv, secret=None, timeout=30, observe=None):
    """No service output, credential or native argv is included in errors."""
    child = None
    def stop(signum, frame):
        raise KeyboardInterrupt
    original = signal.signal(signal.SIGTERM, stop)
    try:
        child = subprocess.Popen(argv, stdin=subprocess.PIPE if secret is not None else subprocess.DEVNULL,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True,
                                 start_new_session=True, env={**os.environ, "LC_ALL": "C.UTF-8"})
        if observe:
            deadline = time.monotonic() + timeout
            while child.poll() is None:
                if observe():
                    return
                if time.monotonic() >= deadline:
                    raise subprocess.TimeoutExpired(argv, timeout)
                time.sleep(.3)
        else:
            child.communicate(secret, timeout=timeout)
        if child.returncode:
            raise Error("The radio action failed")
    except (OSError, subprocess.TimeoutExpired):
        raise Error("The radio action did not complete") from None
    finally:
        if child and child.poll() is None:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait()
        signal.signal(signal.SIGTERM, original)


def request(value):
    try:
        data = json.loads(value)
        if not isinstance(data, dict):
            raise ValueError()
        return data
    except (TypeError, ValueError):
        raise Error("Invalid radio action") from None


def wifi_action(name, value):
    data = request(value)
    snapshot = Wifi().read()
    interface = snapshot["interface"]
    if not interface or data.get("interface") != interface:
        raise Error("The wireless interface is no longer available")
    prefix = ["nmcli", "--wait", "25"]
    if name == "wifi-radio" and type(data.get("enabled")) is bool:
        execute(prefix + ["radio", "wifi", "on" if data["enabled"] else "off"])
        if wifi_device()[0]["enabled"] != data["enabled"]:
            raise Error("The wireless radio did not change")
    elif name == "wifi-scan":
        execute(prefix + ["device", "wifi", "rescan", "ifname", interface])
    else:
        rows = snapshot["networks"] + ([snapshot["linked"]] if snapshot["linked"] else [])
        row = next((row for row in rows if row["id"] == data.get("id")), None)
        if not row:
            raise Error("The wireless network is no longer available")
        if name == "wifi-disconnect" and row["connected"]:
            execute(prefix + ["device", "disconnect", interface])
        elif name == "wifi-forget" and row["uuid"]:
            execute(prefix + ["connection", "delete", "uuid", row["uuid"]])
        elif name == "wifi-connect":
            if row["security"] == "enterprise":
                from .actions import route
                route("open", "omarchy.network")
                return
            secret = None
            if data.get("credentials") is True:
                secret = sys.stdin.readline(258)
                if not secret.endswith("\n") or len(secret) > 257 or any(c in secret[:-1] for c in "\r\n\0"):
                    raise Error("Invalid passphrase input")
            identifier = row["uuid"]
            created = False
            if secret is not None and not identifier:
                raw_ssid = nmprops(row["id"], NM + ".AccessPoint").get("Ssid", [])
                if not raw_ssid or len(raw_ssid) > 32 or any(type(byte) is not int or not 0 <= byte <= 255 for byte in raw_ssid):
                    raise Error("The wireless network is no longer available")
                identifier = str(uuid.uuid4())
                # Public metadata only. D-Bus's byte array preserves SSIDs that
                # cannot be represented by nmcli's text argument. The secret is
                # supplied separately to the activation's stdin below.
                execute(["busctl", "--system", "--timeout=5s", "call", NM, NM_PATH + "/Settings", NM + ".Settings", "AddConnection", "a{sa{sv}}", "3",
                         "connection", "3", "id", "s", row["name"], "type", "s", "802-11-wireless", "uuid", "s", identifier,
                         "802-11-wireless", "1", "ssid", "ay", str(len(raw_ssid)), *[str(byte) for byte in raw_ssid],
                         "802-11-wireless-security", "1", "key-mgmt", "s", "sae" if row["security"] == "sae" else "none" if row["security"] == "wep" else "wpa-psk"])
                created = True
            if identifier:
                activate = prefix + ["connection", "up", "uuid", identifier, "ifname", interface, "ap", row["address"]]
                if secret is not None:
                    # --ask prefills a saved password, so stdin would append to
                    # it. Clear that secret and supply the replacement through
                    # nmcli's password-file parser, backed by stdin, not disk.
                    setting = "802-11-wireless-security." + ("wep-key0" if row["security"] == "wep" else "psk")
                    if not created:
                        execute(prefix + ["connection", "modify", "uuid", identifier, setting, ""])
                    execute(activate + ["passwd-file", "/dev/stdin"], secret=setting + ":" + secret)
                else:
                    execute(activate)
            else:
                execute(prefix + ["device", "wifi", "connect", row["address"], "ifname", interface])
            current = Wifi().read().get("linked")
            if not current or current["address"] != row["address"]:
                raise Error("The wireless connection did not complete")
        else:
            raise Error("The wireless action is no longer available")


def bluetooth_action(name, value):
    data = request(value)
    snapshot = bluetooth()
    if name == "bluetooth-radio" and type(data.get("enabled")) is bool:
        execute(["omarchy-bluetooth-power", "on" if data["enabled"] else "off"])
        if bluetooth()["enabled"] != data["enabled"]:
            raise Error("The Bluetooth radio did not change")
        return
    row = next((row for row in snapshot["devices"] if row["id"] == data.get("id")), None)
    operation = name.removeprefix("bluetooth-")
    if not row or snapshot["adapter"] != data.get("adapter") or operation not in ("pair", "connect", "disconnect", "forget") or not re.fullmatch(r"(?:[\dA-Fa-f]{2}:){5}[\dA-Fa-f]{2}", row["address"]):
        raise Error("The Bluetooth device is no longer available")
    execute(["omarchy-bluetooth-device", operation, row["address"]], timeout=50)
    current = next((item for item in bluetooth()["devices"] if item["id"] == row["id"]), {})
    success = not current if operation == "forget" else current.get("paired") if operation == "pair" else current.get("connected") if operation == "connect" else not current.get("connected")
    if not success:
        raise Error("The Bluetooth device did not change")


def discover():
    if not bluetooth().get("enabled"):
        raise Error("The Bluetooth radio is off")
    # BlueZ owns discovery per client. Killing our bounded client releases only
    # our scan, including when the page disappears or the shell exits.
    execute(["bluetoothctl", "--timeout", "30", "scan", "on"], timeout=33)


def open_login(data):
    url = data.get("AuthURL", "")
    try:
        parsed = urlsplit(url)
        valid = parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not any(char.isspace() for char in url)
    except (ValueError, TypeError):
        valid = False
    if data.get("BackendState") == "NeedsLogin" and valid:
        from .dispatch import native_launch
        if not native_launch(["omarchy-launch-browser", url]):
            raise Error("The login browser is unavailable")
        return True
    return False


def tailnet_action(value):
    if value not in ("start", "stop") or not shutil.which("tailscale"):
        raise Error("The Tailnet action is unavailable")
    if value == "stop":
        execute(["tailscale", "down"])
        if tailnet().get("state") == "Running":
            raise Error("Tailnet did not stop")
        return
    data = status.probe_json(["tailscale", "status", "--json"])
    if open_login(data):
        return
    # The native widget runs the same command and opens its public AuthURL.
    # Read status rather than retaining or forwarding up's diagnostic output.
    login_opened = False
    def observe():
        nonlocal login_opened
        login_opened = open_login(status.probe_json(["tailscale", "status", "--json"]))
        return login_opened
    execute(["tailscale", "up"], timeout=30, observe=observe)
    if not login_opened and tailnet().get("state") != "Running":
        raise Error("Tailnet did not start")
