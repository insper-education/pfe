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
    
    // Clique na barra de menu lateral
    hamburger.addEventListener("click", function(event) {
        if (links_menu_lat.style.display === "block") {
            links_menu_lat.style.display = "none";
        } else {
            links_menu_lat.style.display = "block";
        }
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

});