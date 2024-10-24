/*
  Desenvolvido para o Projeto Final de Engenharia
  Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
  Data: 23 de Outubro de 2024
  Referencia =  https://stackoverflow.com/questions/69470852/how-to-use-js-to-create-an-error-message-that-is-displayed-on-the-user-interface
*/

window.onerror = function (msg, url, lineNo, columnNo, error) {
  var string = String(msg).toLowerCase();
  var substring = "script error";
  if (string.indexOf(substring) > -1){
    alert("Erro de Execução de JavaScript, contactar: lpsoares@insper.edu.br");
  } else {
    var message = [
      "Message: " + msg,
      "URL: " + url,
      "Line: " + lineNo,
      "Column: " + columnNo,
      "Error object: " + JSON.stringify(error),
      "contactar: lpsoares@insper.edu.br"
    ].join(" - ");
    alert(message);
  }
  return false;
};
