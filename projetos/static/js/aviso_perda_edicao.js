/*
  Desenvolvido para o Projeto Final de Engenharia
  Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
  Data: 30 de Agosto de 2024
*/

function aviso_perda_edicao(formSelector, warningMessage) {
  
    var formChanged = false;
    
    if (!formSelector) {  // check if formSelector was provided
      formSelector = "form";
    }

    if (!warningMessage) {  // check if warningMessage was provided
      warningMessage = "Você tem alterações não salvas. Tem certeza que deseja sair?";
    }

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

    // Warn the user if they try to leave the page with unsaved changes.
    // Safari and modern browsers generally ignore custom text and show a default message.
    window.addEventListener("beforeunload", function(event) {
      if (!formChanged) {
        return;
      }

      // Required by some browsers (including Safari) to trigger the native confirmation dialog.
      event.preventDefault();
      // Keep returnValue for cross-browser compatibility (custom text is ignored in modern browsers).
      event.returnValue = warningMessage;
      return warningMessage;
    });

    // Reset formChanged when the form is submitted
    form.addEventListener("submit", function() {
      formChanged = false;
    });
  
}

$(document).ready(function() {
  // Inicia a função de aviso de perda de edição
  aviso_perda_edicao();
});
