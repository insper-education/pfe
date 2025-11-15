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