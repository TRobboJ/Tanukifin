const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const file = path.join(process.argv[2] || 'upstream', 'app/src/main/assets/native/tanukifin-bridge.js');
const source = fs.readFileSync(file, 'utf8');
function boot(origin = 'https://media.example', frame = false) {
    const messages = [];
    const events = {};
    const window = {
        TanukifinBridge: { postMessage: data => messages.push(JSON.parse(data)) },
        addEventListener: (name, fn) => { events[name] = fn; }
    };
    window.top = frame ? {} : window;
    const context = vm.createContext({ window, location: { origin }, URL });
    const config = { origin: 'https://media.example:443', deviceInformation: '{}',
        codecCapabilities: '{}', chromecast: false, nativePlayer: true,
        externalPlayer: false, segmentTypes: '[]' };
    vm.runInContext(`(${source})(${JSON.stringify(config)});`, context);
    return { window, messages, events };
}
const { window: w, messages, events } = boot();
assert.equal(w.NativePlayer.isEnabled(), true);
assert.equal(w.NativeInterface.getDeviceInformation(), '{}');
assert.equal(w.NativeInterface.hasChromecast(), false);
w.NativePlayer.loadPlayer('{"ids":[]}', '{}');
w.NativePlayer.seekMs(1234);
w.MediaSegments.setSegmentTypeAction('Intro', 'Skip');
assert.deepEqual(messages, [
    { method: 'NativePlayer.loadPlayer', args: ['{"ids":[]}', '{}'] },
    { method: 'NativePlayer.seekMs', args: [1234] },
    { method: 'MediaSegments.setSegmentTypeAction', args: ['Intro', 'Skip'] }
]);
assert.equal(w.NativeInterface.openUrl('intent://untrusted'), false);
assert.equal(messages.length, 3);
assert.equal(Object.isFrozen(w.NativeInterface), true);
events['tanukifin-state']({ detail: { nativePlayer: false, externalPlayer: true } });
assert.equal(w.NativePlayer.isEnabled(), false);
assert.equal(w.ExternalPlayer.isEnabled(), true);
for (const foreign of ['http://media.example', 'https://media.example:8096', 'https://evil.test', 'null']) {
    assert.equal(boot(foreign).window.NativeInterface, undefined);
}
assert.equal(boot('https://media.example', true).window.NativeInterface, undefined);
console.log('Bridge bootstrap: origin, frame, command, settings refresh and intent checks passed');
