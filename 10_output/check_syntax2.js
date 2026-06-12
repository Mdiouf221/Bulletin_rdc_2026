const fs = require('fs');
const src = fs.readFileSync('10_output/dashboard_main.js', 'utf8');
try {
    new Function(src);
    console.log('SYNTAX OK');
} catch(e) {
    // Extraire la ligne du message d'erreur
    const lines = src.split('\n');
    // Chercher "ge" ou similaire hors string - chercher la position
    // Node donne un numéro de ligne dans certains cas
    console.error('FULL ERROR:', e.toString().substring(0, 500));
    
    // Chercher toutes les occurrences de "ge" (mangled Âge) hors strings
    const positions = [];
    let inStr = false, strChar = '';
    for (let i = 0; i < src.length; i++) {
        const c = src[i];
        if (!inStr && (c === '"' || c === "'" || c === '`')) { inStr = true; strChar = c; }
        else if (inStr && c === strChar && src[i-1] !== '\\') { inStr = false; }
        else if (!inStr && src.charCodeAt(i) > 127) {
            const ctx = src.substring(Math.max(0, i-50), Math.min(src.length, i+50));
            console.log('Non-ASCII hors string à pos', i, ':', JSON.stringify(ctx));
            if (positions.length > 5) break;
            positions.push(i);
        }
    }
}
