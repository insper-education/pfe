{% comment %}
    Desenvolvido para o Projeto Final de Engenharia
    Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
    Data: 30 de Janeiro de 2021
{% endcomment %}

var table = $('#{{tabela}}').DataTable( {
    dom: "<'row'<'col-md-6'><'col-md-6'f>>t<'row'<'col-md-6'l><'col-md-6'p>>i",
    buttons: [ 'copy', 'csv', 'excel', 'pdf', 'colvis' ],
    lengthMenu: [ [10, 25, 50, 100, -1], [10, 25, 50, 100, "todos"] ],
    stateSave: true,
    language: {
        emptyTable: "Tabela vazia",
        info: "Exibindo _START_ até _END_ de _TOTAL_ itens",
        buttons: {
            colvis: 'Colunas'
        },
        search: "Busca:",
        paginate: {
            first:      "Primeira",
            last:       "Última",
            next:       "Próxima",
            previous:   "Anterior"
        },
        lengthMenu: "Mostrando _MENU_ itens",
    }
} );

table.buttons().container().appendTo( '#{{tabela}}_wrapper .col-md-6:eq(0)' );
