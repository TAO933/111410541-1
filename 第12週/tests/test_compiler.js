'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const { compileFile, compilePath } = require('../JackCompiler');
const root = path.resolve(__dirname, '..');

function fixture(name) {
  const source = path.join(root, 'tests', 'fixtures', name), destination = fs.mkdtempSync(path.join(os.tmpdir(), 'jack-'));
  for (const file of fs.readdirSync(source).filter(file => file.endsWith('.jack'))) fs.copyFileSync(path.join(source, file), path.join(destination, file));
  const outputs = Object.fromEntries(compilePath(destination).map(file => [path.basename(file, '.vm'), fs.readFileSync(file, 'utf8')]));
  fs.rmSync(destination, { recursive: true, force: true }); return outputs;
}

test('Seven generates the canonical reference VM', () => assert.deepEqual(fixture('Seven').Main.trim().split('\n'), [
  'function Main.main 0', 'push constant 1', 'push constant 2', 'add', 'push constant 3', 'add', 'push constant 1', 'add', 'call Output.printInt 1', 'pop temp 0', 'push constant 0', 'return',
]));

test('ArrayTest generates address calculation and array access', () => {
  const output = fixture('ArrayTest').Main;
  assert.match(output, /call Array\.new 1/); assert.match(output, /pop pointer 1\npush temp 0\npop that 0/); assert.match(output, /pop pointer 1\npush that 0/); assert.match(output, /label Main\.WHILE_EXP0/); assert.match(output, /call Output\.printInt 1/);
});

test('Square compiles constructors, methods, and object method calls', () => {
  const outputs = fixture('Square'); assert.deepEqual(Object.keys(outputs).sort(), ['Main', 'Square', 'SquareGame']);
  assert.match(outputs.Square, /function Square\.new 0\npush constant 4\ncall Memory\.alloc 1\npop pointer 0/); assert.match(outputs.Square, /function Square\.moveUp 0\npush argument 0\npop pointer 0/); assert.match(outputs.Square, /call Screen\.drawRectangle 4/); assert.match(outputs.SquareGame, /call Square\.new 3/); assert.match(outputs.SquareGame, /call Square\.moveUp 1/);
});

test('strings, comments, unary operations, and if/else compile', () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'jack-')), file = path.join(directory, 'Main.jack');
  fs.writeFileSync(file, 'class Main { function void main() { var boolean ready; let ready = ~(false); if (ready) { do Output.printString("OK"); } else { do Output.printString("bad"); } return; } }');
  const output = fs.readFileSync(compileFile(file), 'utf8'); fs.rmSync(directory, { recursive: true, force: true });
  assert.match(output, /push constant 2\ncall String\.new 1/); assert.match(output, /push constant 79\ncall String\.appendChar 2/); assert.match(output, /not/); assert.match(output, /label Main\.IF_FALSE0/);
});
