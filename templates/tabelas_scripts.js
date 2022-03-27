{% comment %}
    Desenvolvido para o Projeto Final de Engenharia
    Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
    Data: 30 de Janeiro de 2021
{% endcomment %}

// Atualizar com: $.fn.dataTables.Buttons.stripData
function stripData( str ) {

	if ( typeof str !== 'string' ) {
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

{% comment %} Colocar bancas quando todas as edições {% endcomment %}
var col = -1
var headerObj = $('#{{tabela}}Table').find('th');
for (var i = 0; i < headerObj.length; i +=1){
    if(headerObj.eq(i).text() == "Período") {
        col = i;
    }
}

var table = $('#{{tabela}}Table').DataTable( {
    dom: "<'row mr-1'<'col-md-6'><'col-md-6 d-flex flex-row-reverse'f>>t<'row'<'col-md-6'i><'col-md-6'p>><'row'<'col-sm'><'col-md'><'col-md text-right'l>>",

    {% comment %} Colocar bancas quando todas as edições {% endcomment %}
    createdRow: function( row, data, dataIndex, cells){
        if( $("#filterEdicao option:selected").attr("value") == "todas" ) {            
            if( data[col].slice(-1) ==  '1'){
                $(row).css('background-color', '#D0D0D0');
                $(row).hover(function(){
                    $(this).css('background-color', '#C0C0C0');
                }, function() {
                    $(this).css('background-color', '#D0D0D0');
                });
            }
        }
    },          

{% comment %} 
    $('td').click(function(){
        var col = $(this).prevAll().length;
        var headerObj = $(this).parents('table').find('th').eq(col);
        // A quick test!
        alert("My cell header is called: " + headerObj.text());
        }); {% endcomment %}


    
    buttons: [ 
        
        $.extend( true, {}, buttonCommon, {
            extend: 'copy'
        } ),

        $.extend( true, {}, buttonCommon, {
            extend: 'csv',
            title: 'Projeto Final de Engenharia',
        } ),

        $.extend( true, {}, buttonCommon, {
            extend: 'excel',
            title: 'Projeto Final de Engenharia',
        } ),

        $.extend( true, {}, buttonCommon, {
            extend: 'pdf',
            title: 'Projeto Final de Engenharia',
            orientation: 'landscape',
            pageSize: 'A4',
            text: '<span class="fa fa-file-pdf-o">PDF</span>',
        } ),
        
        'colvis'
    ],
    lengthMenu: [ [10, 25, 50, 100, -1], [10, 25, 50, 100, "todos"] ],
    stateSave: true,
    language: {
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
    }
} );

table.buttons().container().appendTo( '#{{tabela}}Table_wrapper .col-md-6:eq(0)' );
