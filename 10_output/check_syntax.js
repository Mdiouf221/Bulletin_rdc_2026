const fs = require('fs');
const src = fs.readFileSync('10_output/dashboard_main.js', 'utf8');
try {
    new Function(src);
    console.log('SYNTAX OK');
} catch(e) {
    console.error('SYNTAX ERROR:', e.message.substring(0, 300));
}
