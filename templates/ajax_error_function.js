{% comment %}
  Desenvolvido para o Projeto Final de Engenharia
  Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
  Data: 26 de Março de 2024
{% endcomment %}

error: function(request, status, error) {
  if(request.responseText) {
    {% if user.tipo_de_usuario == 4 %} 
      console.log("error"+request.responseText);
      //alert(request.responseText);
    {% endif %}
    jQuery("body").html(request.responseText.replace(/\n/g,"<br>"));
  } else {
    jQuery("body").html("Erro no servidor. Por favor contactar: <a href='mailto:lpsoares@insper.edu.br'>lpsoares@insper.edu.br</a>");
  }
}