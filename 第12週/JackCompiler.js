#!/usr/bin/env node
/* nand2tetris Project 11 Jack-to-VM compiler. No third-party dependencies. */
'use strict';

const fs = require('node:fs');
const path = require('node:path');

const KEYWORDS = new Set('class constructor function method field static var int char boolean void true false null this let do if else while return'.split(' '));
const SYMBOLS = new Set('{}()[].,;+-*/&|<>=~'.split(''));
const OPS = new Set('+-*/&|<>=~'.split(''));
const ARITHMETIC = { '+': 'add', '-': 'sub', '&': 'and', '|': 'or', '<': 'lt', '>': 'gt', '=': 'eq' };
const SEGMENT = { static: 'static', field: 'this', arg: 'argument', var: 'local' };

function syntax(file, line, column, message) { throw new SyntaxError(`${file}:${line}:${column}: ${message}`); }

function tokenize(source, file) {
  const tokens = []; let i = 0, line = 1, column = 1;
  const add = (value, kind, l = line, c = column) => tokens.push({ value, kind, line: l, column: c });
  while (i < source.length) {
    const ch = source[i];
    if (/\s/.test(ch)) { if (ch === '\n') { line++; column = 1; } else column++; i++; continue; }
    if (source.startsWith('//', i)) { while (i < source.length && source[i] !== '\n') { i++; column++; } continue; }
    if (source.startsWith('/*', i)) {
      const startLine = line, startColumn = column; i += 2; column += 2;
      while (i < source.length && !source.startsWith('*/', i)) {
        if (source[i++] === '\n') { line++; column = 1; } else column++;
      }
      if (i === source.length) syntax(file, startLine, startColumn, 'unterminated block comment');
      i += 2; column += 2; continue;
    }
    const startLine = line, startColumn = column;
    if (SYMBOLS.has(ch)) { add(ch, 'symbol'); i++; column++; continue; }
    if (ch === '"') {
      i++; column++; const start = i;
      while (i < source.length && source[i] !== '"') {
        if (/\r|\n/.test(source[i])) syntax(file, startLine, startColumn, 'newline in string constant');
        i++; column++;
      }
      if (i === source.length) syntax(file, startLine, startColumn, 'unterminated string constant');
      add(source.slice(start, i), 'stringConstant', startLine, startColumn); i++; column++; continue;
    }
    if (/\d/.test(ch)) {
      const start = i; while (i < source.length && /\d/.test(source[i])) { i++; column++; }
      const value = source.slice(start, i);
      if (i < source.length && /[A-Za-z0-9_]/.test(source[i])) syntax(file, startLine, startColumn, 'invalid integer constant');
      if (Number(value) > 32767) syntax(file, startLine, startColumn, 'integer constant exceeds 32767');
      add(value, 'integerConstant', startLine, startColumn); continue;
    }
    if (/[A-Za-z_]/.test(ch)) {
      const start = i; while (i < source.length && /[A-Za-z0-9_]/.test(source[i])) { i++; column++; }
      const value = source.slice(start, i); add(value, KEYWORDS.has(value) ? 'keyword' : 'identifier', startLine, startColumn); continue;
    }
    syntax(file, line, column, `unexpected character ${JSON.stringify(ch)}`);
  }
  return tokens;
}

class SymbolTable {
  constructor() { this.classScope = new Map(); this.subScope = new Map(); this.counts = { static: 0, field: 0, arg: 0, var: 0 }; }
  startSubroutine() { this.subScope.clear(); this.counts.arg = this.counts.var = 0; }
  define(name, type, kind) { const entry = { type, kind, index: this.counts[kind]++ }; (kind === 'static' || kind === 'field' ? this.classScope : this.subScope).set(name, entry); }
  count(kind) { return this.counts[kind]; }
  get(name) { return this.subScope.get(name) || this.classScope.get(name); }
}

class Compiler {
  constructor(source, file = '<input>') { this.file = file; this.tokens = tokenize(source, file); this.index = 0; this.symbols = new SymbolTable(); this.vm = []; this.className = ''; this.labelNo = 0; }
  current(offset = 0) { return this.tokens[this.index + offset]; }
  fail(message) { const t = this.current(); if (t) syntax(this.file, t.line, t.column, `${message}; got ${JSON.stringify(t.value)}`); throw new SyntaxError(`${this.file}: unexpected end of file: ${message}`); }
  accept(value) { if (this.current()?.value === value) { this.index++; return true; } return false; }
  expect(value) { if (!this.accept(value)) this.fail(`expected ${JSON.stringify(value)}`); }
  id() { const t = this.current(); if (!t || t.kind !== 'identifier') this.fail('expected identifier'); this.index++; return t.value; }
  type(allowVoid = false) { const t = this.current(); if (t && (t.kind === 'identifier' || ['int', 'char', 'boolean'].includes(t.value) || (allowVoid && t.value === 'void'))) { this.index++; return t.value; } this.fail('expected type'); }
  emit(...words) { this.vm.push(words.join(' ')); }
  label(stem) { return `${this.className}.${stem}${this.labelNo++}`; }
  variable(name) { const variable = this.symbols.get(name); if (!variable) this.fail(`undefined variable ${JSON.stringify(name)}`); return variable; }
  push(variable) { this.emit('push', SEGMENT[variable.kind], variable.index); }
  pop(variable) { this.emit('pop', SEGMENT[variable.kind], variable.index); }
  compile() { this.compileClass(); if (this.current()) this.fail('unexpected token after class declaration'); return `${this.vm.join('\n')}\n`; }
  compileClass() {
    this.expect('class'); this.className = this.id(); this.expect('{');
    while (['static', 'field'].includes(this.current()?.value)) this.compileClassVar();
    while (['constructor', 'function', 'method'].includes(this.current()?.value)) this.compileSubroutine();
    this.expect('}');
  }
  compileClassVar() { const kind = this.current().value; this.index++; const type = this.type(); this.symbols.define(this.id(), type, kind); while (this.accept(',')) this.symbols.define(this.id(), type, kind); this.expect(';'); }
  compileSubroutine() {
    const kind = this.current().value; this.index++; this.type(true); const name = this.id(); this.symbols.startSubroutine();
    if (kind === 'method') this.symbols.define('this', this.className, 'arg');
    this.expect('('); this.compileParameters(); this.expect(')'); this.expect('{');
    while (this.current()?.value === 'var') this.compileVar();
    this.emit('function', `${this.className}.${name}`, this.symbols.count('var'));
    if (kind === 'constructor') { this.emit('push constant', this.symbols.count('field')); this.emit('call Memory.alloc 1'); this.emit('pop pointer 0'); }
    if (kind === 'method') { this.emit('push argument 0'); this.emit('pop pointer 0'); }
    this.compileStatements(); this.expect('}');
  }
  compileParameters() { while (this.current()?.value !== ')') { const type = this.type(); this.symbols.define(this.id(), type, 'arg'); if (!this.accept(',')) break; } }
  compileVar() { this.expect('var'); const type = this.type(); this.symbols.define(this.id(), type, 'var'); while (this.accept(',')) this.symbols.define(this.id(), type, 'var'); this.expect(';'); }
  compileStatements() { const handlers = { let: this.compileLet, if: this.compileIf, while: this.compileWhile, do: this.compileDo, return: this.compileReturn }; while (handlers[this.current()?.value]) handlers[this.current().value].call(this); }
  compileLet() {
    this.expect('let'); const variable = this.variable(this.id()); const array = this.accept('[');
    if (array) { this.push(variable); this.compileExpression(); this.expect(']'); this.emit('add'); }
    this.expect('='); this.compileExpression(); this.expect(';');
    if (array) { this.emit('pop temp 0'); this.emit('pop pointer 1'); this.emit('push temp 0'); this.emit('pop that 0'); } else this.pop(variable);
  }
  compileIf() {
    this.expect('if'); this.expect('('); this.compileExpression(); this.expect(')'); const no = this.label('IF_FALSE'), end = this.label('IF_END');
    this.emit('not'); this.emit('if-goto', no); this.expect('{'); this.compileStatements(); this.expect('}');
    if (this.accept('else')) { this.emit('goto', end); this.emit('label', no); this.expect('{'); this.compileStatements(); this.expect('}'); this.emit('label', end); } else this.emit('label', no);
  }
  compileWhile() {
    this.expect('while'); const start = this.label('WHILE_EXP'), end = this.label('WHILE_END'); this.emit('label', start); this.expect('('); this.compileExpression(); this.expect(')'); this.emit('not'); this.emit('if-goto', end); this.expect('{'); this.compileStatements(); this.expect('}'); this.emit('goto', start); this.emit('label', end);
  }
  compileDo() { this.expect('do'); this.compileCall(); this.expect(';'); this.emit('pop temp 0'); }
  compileReturn() { this.expect('return'); if (this.accept(';')) this.emit('push constant 0'); else { this.compileExpression(); this.expect(';'); } this.emit('return'); }
  compileExpression() { this.compileTerm(); while (OPS.has(this.current()?.value)) { const op = this.current().value; this.index++; this.compileTerm(); if (op === '*') this.emit('call Math.multiply 2'); else if (op === '/') this.emit('call Math.divide 2'); else this.emit(ARITHMETIC[op]); } }
  compileTerm() {
    const t = this.current(); if (!t) this.fail('expected term');
    if (t.kind === 'integerConstant') { this.index++; this.emit('push constant', t.value); return; }
    if (t.kind === 'stringConstant') { this.index++; this.emit('push constant', t.value.length); this.emit('call String.new 1'); for (const char of t.value) { this.emit('push constant', char.charCodeAt(0)); this.emit('call String.appendChar 2'); } return; }
    if (['true', 'false', 'null', 'this'].includes(t.value)) { this.index++; if (t.value === 'true') { this.emit('push constant 0'); this.emit('not'); } else if (t.value === 'this') this.emit('push pointer 0'); else this.emit('push constant 0'); return; }
    if (this.accept('(')) { this.compileExpression(); this.expect(')'); return; }
    if (['-', '~'].includes(t.value)) { this.index++; this.compileTerm(); this.emit(t.value === '-' ? 'neg' : 'not'); return; }
    if (t.kind === 'identifier') {
      const name = this.id();
      if (this.accept('[')) { this.push(this.variable(name)); this.compileExpression(); this.expect(']'); this.emit('add'); this.emit('pop pointer 1'); this.emit('push that 0'); }
      else if (['(', '.'].includes(this.current()?.value)) this.compileCall(name);
      else this.push(this.variable(name));
      return;
    }
    this.fail('expected term');
  }
  compileCall(first = null) {
    let name = first || this.id(), count = 0;
    if (this.accept('.')) { const member = this.id(), variable = this.symbols.get(name); if (variable) { this.push(variable); name = variable.type; count = 1; } name += `.${member}`; }
    else { this.emit('push pointer 0'); name = `${this.className}.${name}`; count = 1; }
    this.expect('('); count += this.compileExpressionList(); this.expect(')'); this.emit('call', name, count);
  }
  compileExpressionList() { let count = 0; if (this.current()?.value !== ')') { do { this.compileExpression(); count++; } while (this.accept(',')); } return count; }
}

function compileFile(file) { const output = file.replace(/\.jack$/i, '.vm'); fs.writeFileSync(output, new Compiler(fs.readFileSync(file, 'utf8'), file).compile(), 'utf8'); return output; }
function compilePath(input) { const stat = fs.statSync(input); const files = stat.isFile() ? [input] : fs.readdirSync(input).filter(file => file.toLowerCase().endsWith('.jack')).sort().map(file => path.join(input, file)); if (!files.length) throw new Error(`No .jack files found at ${input}`); return files.map(compileFile); }
if (require.main === module) { const input = process.argv[2]; if (!input) { console.error('Usage: node JackCompiler.js <file.jack|directory>'); process.exitCode = 2; } else for (const output of compilePath(input)) console.log(output); }
module.exports = { Compiler, compileFile, compilePath, tokenize };
