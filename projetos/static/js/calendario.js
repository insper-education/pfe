/*
  Desenvolvido para o Projeto Final de Engenharia
  Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
  Data: 27 de Outubro de 2024
*/

function mudaVisibilidadeBarras(visibilidade) {
    const action = visibilidade ? "show" : "hide";
    if ($(".lista_operacao").is(":hidden")) {
      $("#titulo_operacao")[action]();
    }
    if ($(".lista_academico").is(":hidden")) {
      $("#titulo_academico")[action]();
    }
    if ($(".lista_aulas").is(":hidden")) {
      $("#titulo_aulas")[action]();
    }
}
  
function ajusta() {
    document.querySelector("#tudo").style.width = "1200px";  
    // Escondendo informações
    mudaVisibilidadeBarras(false);
    carrega_semestre();
}

function reajusta() {
    // Reajustando tela para visualização no browser
    document.querySelector("#tudo").style.width = "100%";
    mudaVisibilidadeBarras(true);
    carrega_semestre();
}

function qual_semestre() {
    if(document.getElementById("primeiro_semestre").style.fontWeight == "bold")
        return 1;
    else
        return 2;
}

function dias_especiais(element, date) {
    var hoje = new Date().toDateString();
    if(date.toDateString() == hoje) {
        $(element).css("outline", "2px solid blue");
        $(element).css("position", "relative");
        $(element).css("z-index", "12");
        $(element).addClass("hoje");
    }
  
    if (date.getDay() === 6 || date.getDay() === 0) { // sábado ou domingo
        $(element).addClass("sem_aula");  
    }
}

var currentYear = 2018; //como se fosse global

// Esconde e mostra meses do semestre
function mostra_semestre(semestre) {
  if (!calendar) { // Conforme o caso, o calendario pode ainda não estar pronto.
    window.setTimeout(() => mostra_semestre(semestre), 100);
    return;
  }

  calendar.render();
  if (semestre === 1) $('*[data-month-id="5"]').nextAll().hide();
  else $('*[data-month-id="6"]').prevAll().remove();

  // Para reduzir o local a só uma linha
  const elements = $(".lin_aulas:visible > :last-child");
  const firstElementText = elements.first().text();
  const allSame = elements.toArray().every(el => $(el).text() === firstElementText || $(el).text() === "");

  if (allSame) {
    $("#barra_local").text(firstElementText);
    $(".header_local, .local").hide();
    $("#barra_inferior").toggle(firstElementText !== "");
    $(".header_aula").css("border-radius", "0 8px 0 0");
  } else {
    $("#barra_local").text("");
    $(".header_local, .local").show();
    $("#barra_inferior").hide();
    $(".header_aula").css("border-radius", "0 0 0 0");
  }
}

function setSemesterStyles(firstSemesterActive) {
  const firstSemester = document.getElementById("primeiro_semestre");
  const secondSemester = document.getElementById("segundo_semestre");

  function setStyles(element, fontWeight, color, background) {
    element.style.fontWeight = fontWeight;
    element.style.color = color;
    element.style.background = background;
  }

  if (firstSemesterActive) {
    setStyles(firstSemester, "bold", "black", "#10F010");
    setStyles(secondSemester, "normal", "grey", "#D0EED0");
  } else {
    setStyles(firstSemester, "normal", "grey", "#D0EED0");
    setStyles(secondSemester, "bold", "black", "#10F010");
  }
  
}

function hideElements() {
  document.querySelectorAll(".semestre").forEach(el => el.style.display = "none");
  $("#linha_lab").hide();
  $("#linha_provas").hide();
}

function showElements(els) {
  els.forEach(el => {
    if (el.classList.contains("lin_aulas")) {
      el.style.display = "table-row";
      if (!el.classList.contains('ano' + currentYear)) el.style.display = "none";
    } else {
      el.style.display = "inline";
    }
    if (el.parentNode.classList.contains("ano" + currentYear)) {
      if (el.classList.contains("lab")) $("#linha_lab").show();
      if (el.classList.contains("prova")) $("#linha_provas").show();
    }
  });
}

function filterAndShowCoordenacao(inicio_semestre, fim_semestre) {
  document.querySelectorAll(".coordenacao").forEach(el => el.style.display = "none");
  let els = Array.from(document.querySelectorAll(".coordenacao[data-mes]"))
    .filter(el => Number(el.dataset.mes) <= fim_semestre && Number(el.dataset.mes) >= inicio_semestre && Number(el.dataset.ano) == currentYear);
  els.forEach(el => el.style.display = "inline");
}

function updateInfoVisibility(fim_semestre, inicio_semestre, isSecondSemester) {
  const filtragem = $(".semestre[data-mes]").filter(function () {
    const no_semestre = isSecondSemester ? $(this).attr("data-mes") > inicio_semestre : $(this).attr("data-mes") <= fim_semestre;
    const no_ano = $(this).parents(".ano" + currentYear).length > 0;
    return no_semestre && no_ano;
  });
  if (filtragem.length > 0) $("#info_semestre").show();
  else $("#info_semestre").hide();
}

function primeiro(e) {
  const inicio_semestre = 1;
  const fim_semestre = 7;
  setSemesterStyles(true);
  hideElements();
  const els = Array.from(document.querySelectorAll(".semestre[data-mes]")).filter(el => Number(el.dataset.mes) < fim_semestre);
  showElements(els);
  filterAndShowCoordenacao(inicio_semestre, fim_semestre);
  updateInfoVisibility(fim_semestre, inicio_semestre, false);
  mostra_semestre(1);
}

function segundo(e) {
  const inicio_semestre = 7;
  const fim_semestre = 13;
  setSemesterStyles(false);
  hideElements();
  const els = Array.from(document.querySelectorAll(".semestre[data-mes]")).filter(el => Number(el.dataset.mes) > inicio_semestre);
  showElements(els);
  filterAndShowCoordenacao(inicio_semestre, fim_semestre);
  updateInfoVisibility(inicio_semestre, 1, true);
  mostra_semestre(2);
}

function carrega_semestre() {
    var today = new Date();
    if(today.getMonth() < 6) {
        primeiro();
    } else {
        segundo();
    }
}

$(document).ready(function() {

    //window.console = window.console || { log: function() {} };
    // Enviar a mensagem de resize para o iframe pai
    if (new URLSearchParams(window.location.search).has("type")) {
      window.parent.postMessage("resize", "*");
    }

    // recarrega a página a cada 6 hora (evita que usuário não veja atualização do dia)
    window.setInterval("location.reload();", 21600000); // 6 hora
    
    // Marca no calendário o dia selecionado
    $(".coordenacao, .semestre").hover(
        function() {
            dia = $(this).data("dia");
            mes = $(this).data("mes") - 1;
            $(".month-container[data-month-id=" + mes + "] div.day-content:not('.hoje')").filter(function() {
            return this.innerHTML == dia;
            }).css({ "boxShadow": "0 0 9px 11px #F0F013", "position": "relative", "z-index": "9" });
        }, 
        function() {
            $("div.day-content:not('.hoje')").css({ "boxShadow": "none", "z-index": "0" })
        }
    );

    document.querySelector('#calendar').addEventListener("yearChanged", function(e) {
        currentYear = e.currentYear;
    
        // Esconde todos os elementos por ano
        [].forEach.call(document.querySelectorAll(".ano"), function (el) {
        el.style.display = 'none';
        });
    
        // Mostra só os elementos do ano
        [].forEach.call(document.querySelectorAll(".ano"+e.currentYear), function (el) {
        if(el.classList.contains("lin_aulas")) { // Preciso fazer isso para a tabela de aulas no final da página
            el.style.display = "table-row";
        } else {
            el.style.display = "inline";
        }
        
        });
        carrega_semestre()
    });

    // Para comutar entre semestres no ano
    document.querySelector("#primeiro_semestre").addEventListener("click", primeiro)
    document.querySelector("#segundo_semestre").addEventListener("click", segundo)
        
    window.onload = carrega_semestre

});
