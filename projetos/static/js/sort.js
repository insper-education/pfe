/*
  Desenvolvido para o Projeto Final de Engenharia
  Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
  Data: 5 de Dezembro de 2024
*/

function parseDate(dateString) {
  var parts = dateString.split("/");
  // Handle two-digit year
  var year = parseInt(parts[2], 10);
  if (year < 100) {
    // If year is less than 100, assume it's in the 2000s
    year += 2000;
  }
  return new Date(year, parts[1] - 1, parts[0]);
}

// Baseado no código de w3.sortHTML
function sort(id, sel, sortvalue, tipo="s") {
  var a, b, i, ii, y, bytt, v1, v2, cc, j; 
  a = document.querySelectorAll(id);
  for (i = 0; i < a.length; i++) {
    for (j = 0; j < 2; j++) {
      cc = 0;
      y = 1;
      while (y == 1) {
        y = 0;
        b = a[i].querySelectorAll(sel);
        for (ii = 0; ii < (b.length - 1); ii++) {
          bytt = 0;
          if (sortvalue) {
            v1 = b[ii].querySelector(sortvalue).innerText.trim();
            v2 = b[ii + 1].querySelector(sortvalue).innerText.trim();
          } else {
            v1 = b[ii].innerText.trim();
            v2 = b[ii + 1].innerText.trim();
          }

          // Tratar valores vazios
          v1 = (v1 === "" || v1 === null) ? null : v1; // Tratar string vazia
          v2 = (v2 === "" || v2 === null) ? null : v2; // Tratar string vazia

          if (tipo=="n") { // number
            v1 = parseFloat(v1);
            v2 = parseFloat(v2);
            // Verificar se v1 ou v2 são NaN e tratá-los    
            if (isNaN(v1)) v1 = Number.NEGATIVE_INFINITY; // Tratar como menor
            if (isNaN(v2)) v2 = Number.NEGATIVE_INFINITY; // Tratar como menor
          } else if (tipo=="d") { // date
            v1 = parseDate(v1);
            v2 = parseDate(v2);
            // Verificar se v1 ou v2 são inválidos
            if (isNaN(v1.getTime())) v1 = new Date(0); // Tratar como menor
            if (isNaN(v2.getTime())) v2 = new Date(0); // Tratar como menor
          } else { // tipo=="s" (string)
            v1 = v1.toLowerCase();
            v2 = v2.toLowerCase();
          }

          if ((j == 0 && (v1 > v2 || (v1 === null && v2 !== null))) || 
              (j == 1 && (v1 < v2 || (v2 === null && v1 !== null)))) {
            bytt = 1;
            break;
          }
        }
        if (bytt == 1) {
          b[ii].parentNode.insertBefore(b[ii + 1], b[ii]);
          y = 1;
          cc++;
        }
      }
      if (cc > 0) {break;}
    }
  }
};
