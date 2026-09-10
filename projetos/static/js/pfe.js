/*
  Desenvolvido para o Projeto Final de Engenharia
  Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
  Data: 23 de Outubro de 2024
*/

// estratégia para imprimir o título da página com underline e não espaço
var tmp_titulo_pagina = document.title;
window.addEventListener("beforeprint", function() {document.title = document.title.replace(/ /g, '_');});
window.addEventListener("afterprint", function() {document.title = tmp_titulo_pagina;}); 

document.addEventListener("DOMContentLoaded", function() {
    var links_menu_lat = document.getElementById("links_menu_lat");
    var hamburger = document.getElementById("hamburger");
    
    // Função auxiliar para abrir/fechar menu
    function toggleMenu(open) {
        if (open) {
            links_menu_lat.style.display = "block";
            hamburger.setAttribute("aria-expanded", "true");
            hamburger.setAttribute("aria-label", "Fechar menu de navegação");
        } else {
            links_menu_lat.style.display = "none";
            hamburger.setAttribute("aria-expanded", "false");
            hamburger.setAttribute("aria-label", "Abrir menu de navegação");
        }
    }
    
    // Clique no botão hamburger
    hamburger.addEventListener("click", function(event) {
        event.stopPropagation(); // Previne propagação para document.click
        var isOpen = links_menu_lat.style.display === "block";
        toggleMenu(!isOpen);
    });

    // Trata quando a tecla Escape é pressionada
    document.addEventListener("keydown", function(event) {
        if (event.key === "Escape" && links_menu_lat.style.display === "block") {
            links_menu_lat.style.display = "none";
        }
    });

    // Esconde o menu ao clicar fora dele
    document.addEventListener("click", function(event) {
        if (links_menu_lat.style.display === "block" && !links_menu_lat.contains(event.target) && !hamburger.contains(event.target)) {
            links_menu_lat.style.display = "none";
        }
    });

    // FECHAR MENSAGEM DE AVISO
    var closeAlertBtn = document.querySelector('.close-alert');
    if (closeAlertBtn) {
        closeAlertBtn.addEventListener('click', function() {
            var mensagem = document.getElementById('mensagem_aviso');
            if (mensagem) {
                mensagem.style.opacity = '0';
                setTimeout(function() {
                    mensagem.remove();
                }, 300);
            }
        });
    }

});

// Exibe um aviso de sucesso transitório (usado para confirmar ações feitas via AJAX,
// já que o django messages framework não é exibido em respostas JSON).
function mostrarAvisoSucesso(mensagemPt, mensagemEn) {
    var main = document.getElementById("main-content");
    if (!main) {
        return;
    }

    var antigo = document.getElementById("mensagem_sucesso");
    if (antigo) {
        antigo.remove();
    }

    var div = document.createElement("div");
    div.id = "mensagem_sucesso";
    div.setAttribute("role", "status");
    div.setAttribute("aria-live", "polite");
    div.setAttribute("aria-atomic", "true");
    div.innerHTML =
        '<i class="fas fa-check-circle" aria-hidden="true"></i>' +
        '<span lang="pt">' + mensagemPt + '</span>' +
        '<span lang="en">' + mensagemEn + '</span>' +
        '<button type="button" class="close-alert" aria-label="Fechar aviso">' +
        '<i class="fas fa-times" aria-hidden="true"></i></button>';

    main.insertBefore(div, main.firstChild);

    if (typeof jQuery !== "undefined") {
        jQuery("#mensagem_sucesso [lang]").each(function() {
            jQuery(this).css("display", "none");
        });
        var lingua = localStorage.getItem("lingua") === "en" ? "en" : "pt";
        jQuery("#mensagem_sucesso [lang='" + lingua + "']").css("display", "initial");
    }

    div.querySelector(".close-alert").addEventListener("click", function() {
        div.remove();
    });

    setTimeout(function() {
        div.style.opacity = "0";
        setTimeout(function() { div.remove(); }, 300);
    }, 6000);
}
