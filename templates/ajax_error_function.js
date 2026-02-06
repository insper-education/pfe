{% comment %}
  Desenvolvido para o Projeto Final de Engenharia
  Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
  Data: 26 de Março de 2024
{% endcomment %}

error: function(request, status, error) {
  if(request.responseText) {
    {% if user.eh_admin %} 
      console.log("error"+request.responseText);
    {% endif %}
    {% if com_alerta %}
      try {
        var response = JSON.parse(request.responseText);
        alert(response.mensagem || request.responseText);
      } catch(e) {
        alert(request.responseText);
      }
    {% else %}
      jQuery("body").html(request.responseText.replace(/\n/g,"<br>"));
    {% endif %}
  } else {
    jQuery("body").html("Erro no servidor. Por favor contactar: <a href='mailto:lpsoares@insper.edu.br'>lpsoares@insper.edu.br</a>");
  }
}