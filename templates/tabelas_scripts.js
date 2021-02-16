{% comment %}
    Desenvolvido para o Projeto Final de Engenharia
    Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
    Data: 30 de Janeiro de 2021
{% endcomment %}

var table = $('#{{tabela}}Table').DataTable( {
    dom: "<'row mr-1'<'col-md-6'><'col-md-6 d-flex flex-row-reverse'f>>t<'row'<'col-md-6'i><'col-md-6'p>><'row'<'col-sm'><'col-md'><'col-md text-right'l>>",
    buttons: [ 'copy', 'csv', 'excel', 'pdf', 'colvis' ],
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
