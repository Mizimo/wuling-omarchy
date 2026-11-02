.pragma library

// Hyprland 0.56's instance signature: commit_epoch-seconds_random, joined
// with underscores. Unknown/private formats fail closed, never guess a login.
function fresh(signature, now) {
    const fields = /^([0-9a-f]{40})_([0-9]{10})_([0-9]+)$/.exec(String(signature));
    if (!fields) return false;
    const age = Number(now) - Number(fields[2]) * 1000;
    return Number.isFinite(age) && age >= 0 && age < 30000;
}
