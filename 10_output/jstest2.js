const fs = require('fs');
const html = fs.readFileSync('10_output/dashboard_regimes.html', 'utf8');
let startIdx = html.indexOf('<script>');
startIdx = html.indexOf('<script>', startIdx + 100);
const endIdx = html.lastIndexOf('</script>');
const js = html.substring(startIdx + 8, endIdx);

// Chercher "ge" dans les labels HTML (dans le JS, pas dans une string)
// Cela peut venir d'une interpolation Python mal fermée
// Chercher le pattern exact: du texte non-JSON hors des constantes
const ageIdx = js.indexOf('\u00c2ge');  // Âge en UTF-8 décodé
const ageIdx2 = js.indexOf('\u00e2ge'); // âge
console.log('Âge trouvé à:', ageIdx, '| âge trouvé à:', ageIdx2);
if (ageIdx > 0) {
    console.log('Contexte:', JSON.stringify(js.substring(Math.max(0,ageIdx-100), ageIdx+100)));
}
if (ageIdx2 > 0) {
    console.log('Contexte âge:', JSON.stringify(js.substring(Math.max(0,ageIdx2-100), ageIdx2+100)));
}

// Chercher toutes les lignes qui contiennent "ge" hors JSON (pas entre guillemets)
// Simplification: chercher dans les 50 premiers ko et les 50 derniers ko hors data
const funcPart = js.substring(js.indexOf('function escapeHtml'));
const ageInFuncs = funcPart.indexOf('\u00c2ge');
const ageInFuncs2 = funcPart.indexOf('\u00e2ge');
console.log('Dans partie fonctions - Âge:', ageInFuncs, '| âge:', ageInFuncs2);
if (ageInFuncs > 0) console.log('Contexte fonctions:', JSON.stringify(funcPart.substring(Math.max(0,ageInFuncs-100), ageInFuncs+100)));
if (ageInFuncs2 > 0) console.log('Contexte fonctions âge:', JSON.stringify(funcPart.substring(Math.max(0,ageInFuncs2-100), ageInFuncs2+100)));