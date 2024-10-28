/*
  Desenvolvido para o Projeto Final de Engenharia
  Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
  Data: 27 de Outubro de 2024
*/


// Função para tratar edição de evento
function editEvent(event) {

    let evento = event.constructor.name === "Event" && event.events.length ? event.events[0] : event;

    $('#event-modal input[name="event-index"]').val(evento ? evento.id : '');
    $('#event-modal select[name="event-type"]').val(evento ? evento.type : '');
    $('#event-modal input[name="event-location"]').val(evento ? evento.location : '');
    $('#event-modal input[name="event-atividade"]').val(evento ? evento.atividade : '');
    $('#event-modal textarea[name="event-descricao"]').val(evento ? evento.descricao : '');
    $('#event-modal input[name="event-observation"]').val(evento ? evento.observation : '');
    $('#event-modal select[name="event-responsavel"]').val(evento ? evento.responsavel : '');      
    $('#event-modal select[name="event-material"]').val(evento ? evento.material : '');
    $('#event-modal select[name="event-material2"]').val(evento ? evento.material2 : '');
    $('#event-modal input[name="event-start-date"]').datepicker('update', evento ? evento.startDate : '');
    $('#event-modal input[name="event-end-date"]').datepicker('update', evento ? evento.endDate : '');

    $('#event-modal input[name="arquivo"]').val(''); // Limpa o campo de arquivo
    
    $(".tooltip-inner").remove();
    $(".tooltip-arrow").remove();

    $("#event-modal").modal();
}

function buscaEditEvent(id) {
    if (id) {
        const dataSource = calendar.getDataSource();
        const event = dataSource.find(event => event.id === id);
        if (event) editEvent(event);
    }
}

function atualiza_visualizacao() {
    dataEventos = [];
    if(!($(".lista_operacao").is(":hidden"))) {
       dataEventos = dataEventos.concat(dataEventosOrganizacao);
    }          
    if(!($(".lista_academico").is(":hidden"))) {
       dataEventos = dataEventos.concat(dataEventosAcademicos);
       calendar.setCustomDayRenderer(dias_especiais);
    } else {
       calendar.setCustomDayRenderer();
    }
    calendar.setDataSource(dataEventos);  // Variavel global calendar
    mostra_semestre(qual_semestre());
}

$("#titulo_operacao").click(function() {
    $(".lista_operacao").toggle( "slide", function(){
        atualiza_visualizacao();
    });
});

$("#titulo_academico").click(function() {
    $(".lista_academico").toggle( "slide" , function(){
        atualiza_visualizacao();
    });
});

$("#titulo_aulas").click(function() {
    $(".lista_aulas").toggle( "slide" , function(){
        atualiza_visualizacao();
    });
});

$(document).ready(function() {
    //let calendar = null;

    //Define o formato para dia/mes/ano em português
    formato_br = {
      format: "dd/mm/yyyy",
      language: "pt-BR",
      daysOfWeekHighlighted: "0,6",
      orientation: "bottom auto",
      autoclose: true,
      showOnFocus: true,
      maxViewMode: 'days',
      keepEmptyValues: true,
      templates: {}
    }

    $('#event-modal input[name="event-start-date"]').datepicker(formato_br);
    $('#event-modal input[name="event-end-date"]').datepicker(formato_br);

    // Botão quando se clica no botão de save do dia    
    $("#save-event").click(function () {
        saveEvent();
    });

});


