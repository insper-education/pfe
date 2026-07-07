/*
  Desenvolvido para o Projeto Final de Engenharia
  Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
  Data: 5 de Dezembro de 2024
*/

function parseDate(dateString) {
  if (!dateString || typeof dateString !== "string") {
    return null;
  }
  var parts = dateString.trim().split("/");
  if (parts.length < 3) {
    return null;
  }
  var day = parseInt(parts[0], 10);
  var month = parseInt(parts[1], 10);
  var year = parseInt(parts[2], 10);
  if (isNaN(day) || isNaN(month) || isNaN(year)) {
    return null;
  }
  if (year < 100) {
    year += 2000;
  }
  var date = new Date(year, month - 1, day);
  if (
    date.getFullYear() !== year ||
    date.getMonth() !== month - 1 ||
    date.getDate() !== day
  ) {
    return null;
  }
  return date;
}

function getSortText(node, sortvalue) {
  var target = sortvalue ? node.querySelector(sortvalue) : node;
  if (!target) {
    return "";
  }
  var text = target.innerText || target.textContent || "";
  return text.trim();
}

function getSortMeta(rawValue, tipo) {
  var empty = rawValue === "" || rawValue === null;

  if (empty) {
    return { empty: true, key: null };
  }

  if (tipo === "n") {
    var numberValue = parseFloat(String(rawValue).replace(",", "."));
    return {
      empty: isNaN(numberValue),
      key: isNaN(numberValue) ? null : numberValue,
    };
  }

  if (tipo === "d") {
    var dateValue = parseDate(rawValue);
    return {
      empty: !dateValue,
      key: dateValue ? dateValue.getTime() : null,
    };
  }

  return {
    empty: false,
    key: String(rawValue).toLowerCase(),
  };
}

function compareEntries(a, b, direction) {
  // Mantém valores vazios por último para evitar resultados confusos.
  if (a.empty && b.empty) {
    return a.index - b.index;
  }
  if (a.empty) {
    return 1;
  }
  if (b.empty) {
    return -1;
  }

  if (a.key < b.key) {
    return -1 * direction;
  }
  if (a.key > b.key) {
    return 1 * direction;
  }
  return a.index - b.index;
}

// Baseado no código de w3.sortHTML
function sort(id, sel, sortvalue, tipo="s") {
  var containers = document.querySelectorAll(id);
  for (var i = 0; i < containers.length; i++) {
    var rows = Array.prototype.slice.call(containers[i].querySelectorAll(sel));
    if (rows.length < 2) {
      continue;
    }

    var entries = rows.map(function(row, index) {
      var rawValue = getSortText(row, sortvalue);
      var meta = getSortMeta(rawValue, tipo);
      return {
        row: row,
        index: index,
        empty: meta.empty,
        key: meta.key,
      };
    });

    // Mantém o comportamento antigo: se já está ascendente, inverte para descendente.
    var alreadyAsc = true;
    for (var j = 0; j < entries.length - 1; j++) {
      if (compareEntries(entries[j], entries[j + 1], 1) > 0) {
        alreadyAsc = false;
        break;
      }
    }

    var direction = alreadyAsc ? -1 : 1;
    entries.sort(function(left, right) {
      return compareEntries(left, right, direction);
    });

    var parent = rows[0].parentNode;
    var fragment = document.createDocumentFragment();
    for (var k = 0; k < entries.length; k++) {
      fragment.appendChild(entries[k].row);
    }
    parent.appendChild(fragment);
  }
};
