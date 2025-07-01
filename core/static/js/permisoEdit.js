/**
 * Este script maneja la funcionalidad de mostrar un formulario de edición en una fila de una tabla
 * cuando se hace clic en un botón de edición.
 * 
 * Funcionalidades incluidas:
 * - Al hacer clic en un botón de la clase 'edit-button', se encuentra la fila correspondiente y se 
 * muestra el formulario de edición dentro de esa fila.
 * 
 */
$('.edit-button').on('click', function () {
    var $row = $(this).closest('tr');
    var $form = $row.find('form'); // Obtén el formulario de edición

    $form.show();
});

/**
 * Este script maneja la funcionalidad de guardar los cambios en un formulario de edición dentro de una fila
 * de una tabla  utilizando AJAX.
 * 
 * Funcionalidades incluidas:
 * - Al hacer clic en un botón con la clase 'save-button', se encuentra la fila correspondiente 
 * y se obtiene el formulario de edición dentro de esa fila. 
 * - Se envía una solicitud AJAX para guardar los cambios utilizando los datos del formulario.
 * - Se oculta el formulario después de enviar la solicitud.
 * 
 */
$('.save-button').on('click', function () {
    var $row = $(this).closest('tr');
    var $form = $row.find('form');
    
    // Enviar una solicitud AJAX para guardar los cambios utilizando el formulario
    $.ajax({
        url: $form.attr('action'),
        method: 'POST',
        data: $form.serialize(),
        success: function (data) {
        }
    });

    $form.hide();
});