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

// Function to convert notation based on language
function convertNotation(data, type, row, meta, lang) {
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

    const numericColumnIndices = getNumericColumnIndices(tableId);
    configuracao_table["columnDefs"] = [{
            targets: numericColumnIndices,
            render: function(data, type, row, meta) {
                return convertNotation(data, type, row, meta, lang);
            }
        }
    ];

    // Se tiver tabela com linguagem o seguinte código ajusta a linguagem da tabela
    document.querySelectorAll("th[data-lang-pt]").forEach(function(th) {
        th.innerHTML = th.getAttribute(lang === "pt" ? "data-lang-pt" : "data-lang-en");
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
