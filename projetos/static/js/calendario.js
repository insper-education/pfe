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
    if ($(".lista_mentorias").is(":hidden")) {
      $("#titulo_mentorias")[action]();
    }
}
  
function ajusta() {
    document.querySelector("#tudo").style.width = "1220px";  
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
function mostra_semestre() {
  if (!calendar) { // Conforme o caso, o calendario pode ainda não estar pronto.
    window.setTimeout(() => mostra_semestre(), 50);
    return;
  }

  calendar.render();

  // Para reduzir o local a só uma linha
  const elements = $(".lin_aulas:visible > :last-child");
  const elements_c = $(".lin_cerimonia:visible > :last-child");
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

function setSemesterStyles(semesterActive) {
  const firstSemester = document.getElementById("primeiro_semestre");
  const secondSemester = document.getElementById("segundo_semestre");

  function setStyles(element, fontWeight, color, background) {
    element.style.fontWeight = fontWeight;
    element.style.color = color;
    element.style.background = background;
  }

  setStyles(firstSemester, "normal", "grey", "#D0EED0");
  setStyles(secondSemester, "normal", "grey", "#D0EED0");

  if (semesterActive == 1) {
    setStyles(firstSemester, "bold", "black", "#10F010");
  }
  
  if (semesterActive == 2) {
    setStyles(secondSemester, "bold", "black", "#10F010");
  }
  
}

function hideElements() {
  document.querySelectorAll(".semestre").forEach(el => el.style.display = "none");
}

function showElements(els) {
  els.forEach(el => {
    if (el.classList.contains("lin_aulas")) {
      el.style.display = "table-row";
      if (!el.classList.contains("ano" + currentYear)) el.style.display = "none";
    } else if (el.classList.contains("lin_mentorias")) {
        el.style.display = "table-row";
        if (!el.classList.contains("ano" + currentYear)) el.style.display = "none";
    } else if (el.classList.contains("lin_cerimonia")) {
        el.style.display = "table-row";
        if (!el.classList.contains("ano" + currentYear)) el.style.display = "none";
    }else {
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
  if (els.length > 0) {
    // Remove o <br> inicial se existir
    els[0].innerHTML = els[0].innerHTML.replace(/^\s*<br\s*\/?>/i, "");
  }
}

function updateInfoVisibility(fim_semestre, inicio_semestre, isSecondSemester) {
  const filtragem = $(".semestre[data-mes]").filter(function () {
    const no_semestre = isSecondSemester ? $(this).attr("data-mes") > inicio_semestre : $(this).attr("data-mes") <= fim_semestre;
    const no_ano = $(this).parents(".ano" + currentYear).length > 0;
    return no_semestre && no_ano;
  });
  if (filtragem.length > 0) {
    $("#info_semestre").show();
    filtragem[0].innerHTML = filtragem[0].innerHTML.replace(/^\s*<br\s*\/?>/i, ""); // Remove o <br> inicial se existir
  }
  else $("#info_semestre").hide();

  // Esconde Mentorias se não houver no semestre
  const mentorias_filtragem = $(".lin_mentorias[data-mes]").filter(function () {
    const no_semestre = isSecondSemester ? $(this).attr("data-mes") > inicio_semestre : $(this).attr("data-mes") <= fim_semestre;
    const no_ano = $(this).attr("data-ano") == currentYear;
    return no_semestre && no_ano;
  });
  if (mentorias_filtragem.length === 0) {
    $("#titulo_mentorias").hide();
    $("#lista_mentorias").hide();
  } else {
    $("#titulo_mentorias").show();
    $("#lista_mentorias").show();
  }

  // Esconde Cerimônias se não houver no semestre
  const cerimonias_filtragem = $(".lin_cerimonia[data-mes]").filter(function () {
    const no_semestre = isSecondSemester ? $(this).attr("data-mes") > inicio_semestre : $(this).attr("data-mes") <= fim_semestre;
    const no_ano = $(this).attr("data-ano") == currentYear;
    return no_semestre && no_ano;
  });
  if (cerimonias_filtragem.length === 0) {
    $("#titulo_encerramento").hide();
    $("#lista_encerramento").hide();
  } else {
    $("#titulo_encerramento").show();
    $("#lista_encerramento").show();
  }

}

function primeiro(e) {
  setSemesterStyles(1);
  const inicio_semestre = 1;
  const fim_semestre = 7;
  hideElements();
  const els = Array.from(document.querySelectorAll(".semestre[data-mes]")).filter(el => Number(el.dataset.mes) < fim_semestre);
  showElements(els);
  filterAndShowCoordenacao(inicio_semestre, fim_semestre);
  updateInfoVisibility(fim_semestre, inicio_semestre, false);
  mostra_semestre();
}

function segundo(e) {
  setSemesterStyles(2);
  const inicio_semestre = 7;
  const fim_semestre = 12;
  hideElements();
  const els = Array.from(document.querySelectorAll(".semestre[data-mes]")).filter(el => Number(el.dataset.mes) > inicio_semestre);
  showElements(els);
  filterAndShowCoordenacao(inicio_semestre, fim_semestre);
  updateInfoVisibility(fim_semestre, inicio_semestre, true);
  mostra_semestre();
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

    document.querySelector("#calendar").addEventListener("yearChanged", function(e) {
      currentYear = e.currentYear;
    
      // Esconde todos os elementos por ano
      [].forEach.call(document.querySelectorAll(".ano"), function (el) {
        el.style.display = "none";
      });
    
      // Mostra só eventos do ano
      [].forEach.call(document.querySelectorAll(".ano"+e.currentYear), function (el) {
        if(el.classList.contains("lin_aulas")) { // Preciso fazer isso para a tabela de aulas no final da página
          el.style.display = "table-row";
        } else if(el.classList.contains("lin_mentorias")) {
          el.style.display = "table-row";
        } else if(el.classList.contains("lin_cerimonia")) {
          el.style.display = "table-row";
        } else {
          el.style.display = "inline";
        }
      });

      carrega_semestre();

    });

    // Para comutar entre semestres no ano
    document.querySelector("#primeiro_semestre").addEventListener("click", primeiro)
    document.querySelector("#segundo_semestre").addEventListener("click", segundo)
        
    window.onload = carrega_semestre

});
