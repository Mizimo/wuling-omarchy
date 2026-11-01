#!/usr/bin/env node
// Run only inside the disposable VM. Uses the installed *internal* model as
// a diagnostic oracle; this is not a supported plugin API or product adapter.
const fs = require('node:fs');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const root = process.env.OMARCHY_PATH || '/usr/share/omarchy';
const model = require(path.join(root, 'shell/plugins/menu/MenuModel.js'));
const read = p => fs.existsSync(p) ? fs.readFileSync(p, 'utf8') : '';
const defaults = model.parseMenuJsonc(read(path.join(root, 'default/omarchy/omarchy-menu.jsonc')));
const extensions = model.parseMenuJsonc(read(path.join(process.env.HOME, '.config/omarchy/extensions/omarchy-menu.jsonc')));
const merged = model.mergeMenuSources(defaults, extensions);
const script = model.guardScript(merged.items);
const guards = spawnSync('bash', ['-lc', script], {encoding:'utf8', timeout:30000});
if (guards.error || guards.status !== 0) throw new Error('Guard evaluation failed');
const results = {};
const checked = {};
for (const line of guards.stdout.split('\n')) {
    const match = /^(.*):([wc]):([01])$/.exec(line);
    if (match) (match[2] === 'w' ? results : checked)[match[1]] = match[3] === '1';
}
console.log(JSON.stringify({internalModel: true, staticOnly: true,
    defaultCount: defaults.length, extensionCount: extensions.length,
    rows: merged.itemOrder.map(id => ({...merged.items[id],
        checkedResult: checked[id] === true,
        displayLabel: model.labelFor(merged.items[id], checked),
        visible: model.isVisible(merged.items, merged.itemOrder, results, merged.items[id])}))}, null, 2));
