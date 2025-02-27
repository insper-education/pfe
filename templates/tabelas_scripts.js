{% comment %}
  Desenvolvido para o Projeto Final de Engenharia
  Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
  Data: 30 de Janeiro de 2021
{% endcomment %}

// Atualizar com: $.fn.dataTables.Buttons.stripData
function stripData( str ) {

	if ( typeof str !== "string" ) {
		return str;
	}

	// Always remove script tags
	str = str.replace( /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '' );

	// Always remove comments
	str = str.replace( /<!\-\-.*?\-\->/g, '' );

    str = str.replace( /&nbsp;/g, ' ' );
    str = str.replace( /🔗/g, '' );

    str = str.replace( /&amp;/g, '&' );
    

    str = str.replace( /<[^>]*>/g, '' );
	str = str.replace( /^\s+|\s+$/g, '' );
	str = str.replace( /\n/g, ' ' );

    str = str.replace( /&lt;/g, '<' );
    str = str.replace( /&gt;/g, '>' );

    //str = str.replace( /<br\s*\/?>/ig, "\r\n" );

	return str;
};

var buttonCommon = {
    exportOptions: {
        format: {
            body: function ( data, row, column, node ) {
                return stripData(data);
            }
        },
        columns: ':visible'
    }
};

{% comment %} Colocar periodos quando todas as edições {% endcomment %}
var col = -1
var headerObj = $("#{{tabela}}Table").find("th");
for (var i = 0; i < headerObj.length; i +=1){
    if(headerObj.eq(i).text() == "Período") {
        col = i;
    }
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
            extend: 'copy'
        } ),

        $.extend( true, {}, buttonCommon, {
            extend: 'csv',
            title: titulo_arquivo,
        } ),

        $.extend( true, {}, buttonCommon, {
            extend: 'excel',
            title: titulo_arquivo,
        } ),

        $.extend( true, {}, buttonCommon, {
            extend: 'pdf',
            title: titulo_arquivo,
            orientation: 'landscape',
            pageSize: 'A4',
            text: '<span class="fa fa-file-pdf-o">PDF</span>',
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
        if ($(this).data("tipo") === "numeral") {
            indices.push(i);
        }
    });
    return indices;
}

function convertNotation(data, type, row, meta, lang) {
    if (type === "display" || type === "filter") {
        if (lang === "en") return data.replace(',', '.');
        else if (lang === "pt") return data.replace('.', ',');
    }
    return data;
}

// function to update the language
function atualiza_lingua(lang) {
    // Primeiro Destruir a tabela
    var tableId = "#{{tabela}}Table";
    if ($.fn.DataTable.isDataTable(tableId)) {
        $(tableId).DataTable().destroy();
    }

    var numericColumnIndices = getNumericColumnIndices(tableId);
    configuracao_table["columnDefs"] = [{
            targets: numericColumnIndices, // Replace with the indices of your numeric columns
            render: function(data, type, row, meta) {
                return convertNotation(data, type, row, meta, lang);
            }
        }
    ];

    // Se tiver tabela com linguagem o seguinte código ajusta a linguagem da tabela
    document.querySelectorAll("th[data-lang-pt]").forEach(function(th) {
        if (lang === "pt") {
            th.innerHTML = th.getAttribute("data-lang-pt");
        } else if (lang === "en") {
            th.innerHTML = th.getAttribute("data-lang-en");
        }
    });
  

    // Setar a nova linguagem
    configuracao_table["language"] = textos_linguas[lang];
    table = $("#{{tabela}}Table").DataTable(configuracao_table);
    table.buttons().container().appendTo( "#{{tabela}}Table_wrapper .col-md-6:eq(0)" );
}

$(document).ready(function() {
    $("body").on("click", "#language_button", function(e) {
        lingua_atual = localStorage.getItem("lingua");
        atualiza_lingua(lingua_atual);
    });
});

lingua_atual = localStorage.getItem("lingua");
atualiza_lingua(lingua_atual);
