/*
  Desenvolvido para o Projeto Final de Engenharia
  Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
  Data: 30 de Agosto de 2024
*/

function aviso_perda_edicao(formSelector, warningMessage) {
  document.addEventListener("DOMContentLoaded", function() {
    var formChanged = false;
    var form = document.querySelector(formSelector);

    if (!form) {
      console.warn("Form not found for the provided selector.");
      return;
    }

    // Detect changes in all input elements
    form.querySelectorAll("input, textarea, select").forEach(function(element) {
      element.addEventListener("input", function() {
        formChanged = true;
      });
      element.addEventListener("change", function() {
        formChanged = true;
      });
    });

    // Warn the user if they try to leave the page with unsaved changes
    window.addEventListener("beforeunload", function(event) {
      if (formChanged) {
        event.returnValue = warningMessage; // For compatibility with older browsers
        return warningMessage; // For some browsers
      }
    });

    // Reset formChanged when the form is submitted
    form.addEventListener("submit", function() {
      formChanged = false;
    });
  });
}