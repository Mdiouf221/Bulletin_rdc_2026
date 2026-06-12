const fs = require('fs');
const html = fs.readFileSync('10_output/dashboard_regimes.html', 'utf8');
let startIdx = html.indexOf('<script>');
startIdx = html.indexOf('<script>', startIdx + 100);
const endIdx = html.lastIndexOf('</script>');
const js = html.substring(startIdx + 8, endIdx);

try {
    new Function(js);
    console.log('SYNTAX OK');
} catch(e) {
    const lines = js.split('\n');
    const match = e.stack ? e.stack.match(/<anonymous>:(\d+):(\d+)/) : null;
    const lineNum = match ? parseInt(match[1]) : -1;
    const colNum  = match ? parseInt(match[2]) : -1;
    console.error('ERREUR: ' + e.message + ' (ligne ' + lineNum + ', col ' + colNum + ')');
    if (lineNum > 0) {
        for (let i = Math.max(0, lineNum-3); i <= Math.min(lines.length-1, lineNum+2); i++) {
            const marker = (i+1 === lineNum) ? '>>>' : '   ';
            console.log(marker + ' L' + (i+1) + ': ' + lines[i].substring(0, 150));
        }
    }
}