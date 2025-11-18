{% comment %}
  Desenvolvido para o Projeto Final de Engenharia
  Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
  Data: 30 de Janeiro de 2021
{% endcomment %}

// Atualizar com: $.fn.dataTables.Buttons.stripData
function stripData(str) {
    if (typeof str !== "string") return str;
    return str
        .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')  {% comment %} Always remove script tags {% endcomment %}
        .replace(/<!\-\-.*?\-\->/g, '') {% comment %} Always remove comments {% endcomment %}
        .replace(/&nbsp;/g, ' ')
        .replace(/🔗/g, '')
        .replace(/&amp;/g, '&')
        .replace(/<[^>]*>/g, '')
        .replace(/^\s+|\s+$/g, '')
        .replace(/\n/g, ' ')
        .replace(/&lt;/g, '<').replace(/&gt;/g, '>');
}

const buttonCommon = {
    exportOptions: {
        format: {
            body: (data, row, column, node) => stripData(data)
        },
        columns: ":visible"
    }
};

{% comment %} Colocar periodos quando todas as edições {% endcomment %}
var col = -1
var headerObj = $("#{{tabela}}Table").find("th");
for (var i = 0; i < headerObj.length; i +=1){
    if(headerObj.eq(i).text() == "Período") col = i;
}

var titulo_arquivo = "Capstone";

var textos_linguas = {
    pt: {
        decimal:        "",
        emptyTable:     "Tabela vazia",
        info:           "Exibindo de _START_ até _END_ em _TOTAL_ {{tabela}}",
        infoEmpty:      "Exibindo de 0 até 0 em 0 {{tabela}}",
        infoFiltered:   "(filtrado de _MAX_ {{tabela}})",
        infoPostFix:    "",
        thousands:      "",
        lengthMenu:     "Mostrando _MENU_ itens",
        loadingRecords: "Carregando...",
        processing:     "Processando...",
        search:         "Busca:",
        zeroRecords:    "Não foram encontrados registros com a busca",
        paginate: {
            first:      "Primeira",
            last:       "Última",
            next:       "Próxima",
            previous:   "Anterior"
        },
        aria: {
            sortAscending:  ": ativado para ordenar a coluna de forma ascendente",
            sortDescending: ": ativado para ordenar a coluna de forma descendente"
        },
        buttons: {
            colvis: 'Colunas'
        }
    },
    en: {
        decimal:        "",
        emptyTable:     "No data available",
        info:           "Showing _START_ to _END_ of _TOTAL_ {{tabela}}",
        infoEmpty:      "Showing 0 to 0 of 0 {{tabela}}",
        infoFiltered:   "(filtered from _MAX_ total {{tabela}})",
        infoPostFix:    "",
        thousands:      "",
        lengthMenu:     "Show _MENU_ items",
        loadingRecords: "Loading...",
        processing:     "Processing...",
        search:         "Search:",
        zeroRecords:    "No matching records found",
        paginate: {
            first:      "First",
            last:       "Last",
            next:       "Next",
            previous:   "Previous"
        },
        aria: {
            sortAscending:  ": activate to sort column ascending",
            sortDescending: ": activate to sort column descending"
        },
        buttons: {
            colvis: 'Columns'
        }
    }
};

/** Quando exportando, função obtem o texto visível de um nó, considerando a língua atual. **/
function getVisibleTextInNode(node) {
  console.log(node);
  var text = '';
  const lingua = localStorage.getItem("lingua"); // Identifica a língua atual
  $(node).contents().each(function() {
    if (this.nodeType === 3) { // Se for um texto puro só adiciona o texto
      text += this.nodeValue;
    } else if (!$(this).attr("lang") || $(this).attr("lang") === lingua) {  // Se não tiver atributo lang ou for igual à língua atual adiciona o texto
      text += $(this).text();
    }
  });
  return text.replace(/[\r\n]+/g, ' ').trim();
}

{% comment %} 
/** Quando exportando, função obtem o texto visível de um nó, considerando a língua atual e visibilidade no DOM. **/
function getVisibleTextInNode(node) {
  if (!node) return '';
  const lingua = localStorage.getItem("lingua") || "pt";
  let out = '';

  function isVisible(el) {
    const $el = $(el);
    if (!$el.is(':visible')) return false;              // display:none, visibility:hidden, d-none, etc.
    if ($el.attr('aria-hidden') === 'true') return false;
    return true;
  }

  function walk(n) {
    if (!n) return;

    if (n.nodeType === 3) { // Text node
      // Só inclui se toda a cadeia de pais for visível e a língua não conflitar
      let el = n.parentNode;
      while (el && el.nodeType === 1) {
        const $el = $(el);
        const langAttr = $el.attr('lang');
        if (langAttr && langAttr !== lingua) return;
        if (!isVisible(el)) return;
        if ($el.hasClass('no-export')) return; // opcional: permita marcar trechos que nunca devem exportar
        el = el.parentNode;
      }
      out += n.nodeValue;
      return;
    }

    if (n.nodeType === 1) { // Elemento
      const $n = $(n);
      const langAttr = $n.attr('lang');
      if (langAttr && langAttr !== lingua) return;
      if (!isVisible(n)) return;
      if ($n.hasClass('no-export')) return;

      for (let i = 0; i < n.childNodes.length; i++) {
        walk(n.childNodes[i]);
      }
    }
  }

  walk(node);
  return out.replace(/[\r\n]+/g, ' ').replace(/\s+/g, ' ').trim();
} {% endcomment %}



var configuracao_table = {
    dom: "<'row mr-1'<'col-md-6'><'col-md-6 d-flex flex-row-reverse'f>>t<'row'<'col-md-6'i><'col-md-6'p>><'row'<'col-sm'><'col-md'><'col-md text-right'l>>",

    {% comment %} Colocar bancas quando todas as edições {% endcomment %}
    createdRow: function( row, data, dataIndex, cells){
        if( $("#filterEdicao option:selected").attr("value") == "todas" ) {            
            if( data[col] != null && data[col].slice(-1) ==  '1'){
                $(row).css("background-color", "#D0D0D0");
                $(row).hover(function(){
                    $(this).css("background-color", "#C0C0C0");
                }, function() {
                    $(this).css("background-color", "#D0D0D0");
                });
            }
        }
    },
    buttons: [ 
        
        $.extend( true, {}, buttonCommon, {
            extend: "copy",
            exportOptions: {
              format: {
                body: function (data, row, column, node) {
                  return getVisibleTextInNode(node);
                }
              }
            }
        } ),

        $.extend( true, {}, buttonCommon, {
            extend: "csv",
            title: titulo_arquivo,
            fieldBoundary: '"',
            fieldSeparator: ',',
            exportOptions: {
              format: {
                body: function (data, row, column, node) {
                  return getVisibleTextInNode(node);
                }
              }
            }
        } ),

        $.extend( true, {}, buttonCommon, {
            text: "JSON",
            filename: titulo_arquivo,
            action: function (e, dt, node, config) {
                var data = dt.buttons.exportData($.extend(true, {}, config.exportOptions));
                var json = JSON.stringify(data, null, 2);
                var blob = new Blob([json], {type: "application/json"});
                var url = URL.createObjectURL(blob);
                var a = document.createElement('a');
                a.href = url;
                a.download = (config.filename || "datatable") + ".json";
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            },
            exportOptions: {
              format: {
                body: function (data, row, column, node) {
                  return getVisibleTextInNode(node);
                }
              }
            }
        } ),

        $.extend( true, {}, buttonCommon, {
            extend: "excel",
            title: titulo_arquivo,
            exportOptions: {
              format: {
                body: function (data, row, column, node) {
                  return getVisibleTextInNode(node);
                }
              }
            }
        } ),

        $.extend( true, {}, buttonCommon, {
            extend: "pdf",
            title: titulo_arquivo,
            orientation: "landscape",
            pageSize: "A4",
            text: '<span class="fa fa-file-pdf-o">PDF</span>',
            exportOptions: {
              format: {
                body: function (data, row, column, node) {
                  return getVisibleTextInNode(node);
                }
              }
            }
        } ),
        
        'colvis'
    ],
    lengthMenu: [ [10, 25, 50, 100, -1], [10, 25, 50, 100, "todos"] ],
    stateSave: true,
    columnDefs: [  {% comment %} Para ordenar com os acentos {% endcomment %}
        { type: 'chinese-string', targets: 0 }
    ],

    language: textos_linguas["pt"],

    drawCallback: function(settings) {
        $("[data-toggle='tooltip']").tooltip("dispose").tooltip({trigger : "hover", boundary: "window"});  {% comment %} <script src="{% static 'js/tooltip.js' %}"></script> {% endcomment %}
    },

};

function getNumericColumnIndices(tableId) {
    var indices = [];
    $(tableId + " th").each(function(i) {
        if ($(this).data("tipo") === "numeral") indices.push(i);
    });
    return indices;
}

function getDateHourColumnIndices(tableId) {
    var indices = [];
    $(tableId + " th").each(function(i) {
        if ($(this).data("tipo") === "data_hora") indices.push(i);
    });
    return indices;
}

function getHiddenColumnIndices(tableId) {
    var indices = [];
    $(tableId + " th").each(function(i) {
        var attr = $(this).attr("data-esconder");
        if (attr !== undefined && attr !== "false" && attr !== "0") {
            indices.push(i);
        }
    });
    return indices;
}

function getDefaultOrderFromHeaders(tableId) {
    var order = [];
    $(tableId + " thead th").each(function(i) {
        var dir = (($(this).attr("data-ordenamento") || "") + "").toLowerCase();
        if (dir === "asc" || dir === "desc") order.push([i, dir]);
    });
    return order;
}

// Robust date parser: returns a numeric timestamp for sorting (ms since epoch)
// Supports:
// - data-order attribute (ISO, YYYY-MM-DD, YYYY-MM-DD HH:mm[:ss])
// - dd/mm/yyyy[ HH:mm[:ss]] (PT/BR style)
// - ISO strings (YYYY-MM-DD[T]HH:mm[:ss])
// Returns NaN if it cannot parse.
function toTimestampForSort(value) {
    if (value == null) return NaN;
    if (value instanceof Date) return value.getTime();
    if (typeof value === "number") return value; // assume already ts
    var str = String(value).trim();
    try { str = stripData(str); } catch (e) {}
    if (!str) return NaN;

    // Extract first dd/mm/yyyy (optionally with time) from anywhere in string
    var m = str.match(/([0-3]?\d)\/([0-1]?\d)\/(\d{2}|\d{4})(?:\s+([0-2]?\d):([0-5]?\d)(?::([0-5]?\d))?)?/);
    if (m) {
        var d = parseInt(m[1], 10);
        var mo = parseInt(m[2], 10) - 1; // 0-based month
        var y = parseInt(m[3], 10);
        if (y < 100) y += 2000; // assume 20xx for 2-digit year
        var hh = m[4] ? parseInt(m[4], 10) : 0;
        var mm = m[5] ? parseInt(m[5], 10) : 0;
        var ss = m[6] ? parseInt(m[6], 10) : 0;
        var dt = new Date(y, mo, d, hh, mm, ss);
        return dt.getTime();
    }

    // Try ISO/Date.parse as fallback
    var iso = Date.parse(str);
    if (!isNaN(iso)) return iso;

    return NaN;
}

// Build fresh columnDefs for numeric and date types without losing existing ones
function buildTypedColumnDefs(lang, tableId) {
    var baseDefs = (configuracao_table["columnDefs"] || []).filter(function(def) {
        // Remove previously injected defs to avoid duplicates on re-init
        return def.name !== "numeric-render" && def.name !== "date-render";
    });

    var numericColumnIndices = getNumericColumnIndices(tableId);
    if (numericColumnIndices.length) {
        baseDefs.push({
            name: "numeric-render",
            targets: numericColumnIndices,
            type: "num",
            // Format visible text (display) while preserving HTML
            createdCell: function(td, cellData, rowData, row, col) {
                var lang = localStorage.getItem("lingua") || "pt";
                var html = $(td).html();
                var text = $(td).text();
                var formatted = convertNotation(text || "", "display", rowData, { row: row, col: col }, lang);
                var m = text.match(/-?\d+(?:[.,]\d+)?/);
                if (m) {
                    $(td).html(html.replace(m[0], formatted));
                }
            },
            // Sort fallback when data-order is missing
            render: function(data, type, row, meta) {
                if (type === "sort" || type === "type") {
                    var cell = meta && meta.settings && meta.settings.aoData && meta.settings.aoData[meta.row] && meta.settings.aoData[meta.row].anCells
                        ? meta.settings.aoData[meta.row].anCells[meta.col]
                        : null;
                    if (cell) {
                        var ord = $(cell).attr("data-order") || $(cell).attr("data-sort");
                        if (ord != null && ord !== "") {
                            return parseFloat(String(ord).replace(',', '.'));
                        }
                    }
                    if (data == null) return NaN;
                    return parseFloat(String(stripData(data)).replace(',', '.'));
                }
                // For DOM source, display render is ignored by design
                return data;
            }
        });
    }

    var dateColumnIndices = getDateHourColumnIndices(tableId);
    if (dateColumnIndices.length) {
        baseDefs.push({
            name: "date-render",
            targets: dateColumnIndices,
            // We return a numeric timestamp for sorting, so force numeric type
            type: "num",
            render: function(data, type, row, meta) {
                if (type === "sort" || type === "type") {
                    var cell = meta && meta.settings && meta.settings.aoData && meta.settings.aoData[meta.row] && meta.settings.aoData[meta.row].anCells
                        ? meta.settings.aoData[meta.row].anCells[meta.col]
                        : null;
                    var ts;
                    if (cell && $(cell).attr("data-order")) {
                        ts = toTimestampForSort($(cell).attr("data-order"));
                    } else {
                        // fallback: tenta converter o próprio data (dd/mm/yyyy, ISO, etc.)
                        ts = toTimestampForSort(data);
                    }
                    // Garantir valor numérico para ordenar; valores inválidos vão para o final
                    return isNaN(ts) ? Number.MAX_SAFE_INTEGER : ts;
                }
                // Para display e filter
                return data;
            }
        });
    }

    var hiddenColumnIndices = getHiddenColumnIndices(tableId);
    if (hiddenColumnIndices.length) {
        baseDefs.push({
            name: "hidden-columns",
            targets: hiddenColumnIndices,
            visible: false
        });
    }

    return baseDefs;
}


// Function to convert notation based on language
function convertNotation(data, type, row, meta, lang) {
    // Para ordenação e tipo, sempre retorna número puro (com ponto)
    if (type === "sort" || type === "type") {
        if (typeof data === "string") {
            // Troca vírgula por ponto e remove espaços
            return parseFloat(data.replace(',', '.').replace(/\s/g, ''));
        }
        return data;
    }
    // Para exibição e filtro, trata conforme o idioma
    if (type === "display" || type === "filter") {
        if (lang === "en") return data.replace(',', '.');
        if (lang === "pt") return data.replace('.', ',');
    }
    return data;
}

function updateTableLanguageSpans(lang) {
    $("#{{tabela}}Table td, #{{tabela}}Table th").each(function() {
        $(this).find("[lang]").each(function() {
            $(this).css("display", $(this).attr("lang") === lang ? "initial" : "none");
        });
    });
}

// function to update the language
function atualiza_lingua(lang) {

    // Primeiro Destruir a tabela
    const tableId = "#{{tabela}}Table";
    if ($.fn.DataTable.isDataTable(tableId)) {
        $(tableId).DataTable().destroy();
    }

    // Reconstrói defs de colunas numéricas e de data sem sobrescrever outras defs existentes
    configuracao_table["columnDefs"] = buildTypedColumnDefs(lang, tableId);

    // Define ordem padrão a partir dos headers (se houver e é ignorado se houver no state)
    var defaultOrder = getDefaultOrderFromHeaders(tableId);
    configuracao_table.order = defaultOrder.length ? defaultOrder : [[0, 'asc']];

    // Se tiver tabela com linguagem o seguinte código ajusta a linguagem da tabela
    document.querySelectorAll("th[data-lang-pt]").forEach(function(th) {
        texto_lingua = th.getAttribute(lang === "pt" ? "data-lang-pt" : "data-lang-en")
        texto = th.getAttribute("data-texto");
        icone = th.getAttribute("data-icone");
        if (icone) {
            texto_lingua = '<span class="th-icone">' + icone  + '</span><span class="th-nao-icone">' + texto_lingua + '</span>';
        }
        th.innerHTML = texto_lingua + (texto ? '<span>' + texto + '</span>' : '');
    });
  
    // Setar a nova linguagem
    configuracao_table["language"] = textos_linguas[lang];  // Tabela gigante com os textos de cada língua
    table = $("#{{tabela}}Table").DataTable(configuracao_table);
    table.buttons().container().appendTo( "#{{tabela}}Table_wrapper .col-md-6:eq(0)" );

    // Update all spans for the selected language
    updateTableLanguageSpans(lang);

    // Also update spans after every table redraw (e.g., after filtering)
    table.on("draw", function() {
        updateTableLanguageSpans(lang);
    });

}

$(document).ready(function() {
    $("body").on("click", "#language_button", function() {
        atualiza_lingua(localStorage.getItem("lingua"));
    });
    atualiza_lingua(localStorage.getItem("lingua"));
});
