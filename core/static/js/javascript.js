/**
 * Funcionalidad que inicia eventos y funcionalidades de las ventanas modales para Permisos y Licencias.
 * 
 * Esta funcionalidad tiene como objetivo dar el funcionamiento a las ventanas modal de crear permios y licencias
 * para abrirlas y cerrarlas. Las modales se pueden abrir al hacer clic en su respectivo boton y se pueden cerrar
 * al hacer clic en sus botones o al hacer clic fuera de la ventana.
 * 
 */
document.addEventListener("DOMContentLoaded", function () {
    const crearPermisoBtn = document.getElementById("crear-permiso");
    const permisoModal = document.getElementById("permiso-modal");
    const cerrarModalPermisosBtn = document.getElementById("cerrar-modal-permisos");

    const crearLicenciaBtn = document.getElementById("crear-licencia");
    const licenciaModal = document.getElementById("licencia-modal");
    const cerrarModalLicenciasBtn = document.getElementById("cerrar-modal-licencias");

    // Función para mostrar la ventana modal
    function mostrarModal(modal) {
        modal.style.display = "block";
        setTimeout(function () {
        }, 10);
    }

    // Función para cerrar la ventana modal
    function cerrarModal(modal) {
        modal.style.display = "none";
    }

    // Función para cerrar el modal haciendo clic afuera
    function cerrarModalAfueras(e) {
        if (e.target === permisoModal) {
            cerrarModal(permisoModal);
        }
        if (e.target === licenciaModal) {
            cerrarModal(licenciaModal);
        }
    }

    // Asignar eventos a botones y elementos
    crearPermisoBtn.addEventListener("click", function (event) {
        event.preventDefault();
        mostrarModal(permisoModal);
    });

    cerrarModalPermisosBtn.addEventListener("click", function () {
        cerrarModal(permisoModal);
    });

    crearLicenciaBtn.addEventListener("click", function (event) {
        event.preventDefault();
        mostrarModal(licenciaModal);
    });

    cerrarModalLicenciasBtn.addEventListener("click", function () {
        cerrarModal(licenciaModal);
    });

    window.addEventListener("click", cerrarModalAfueras);
});

// Formularios permisos y licencias: hace que los campos fecha inicio y fecha fin permita seleccionar los dias en forma de calendario
$(function () {
    $(".datepicker").datepicker({
        format: 'dd/mm/yyyy',
    });
});
// Fin

//Mostrar las fechas en formato año-mes-dia (se usa para la columna Creado)
$.fn.dataTable.moment('YYYY-MM-DD');
//Fin

/**
 * TABLA VER PERMISOS 
 * 
 * Inicializa una tabla con DataTables y configura varias opciones:
 * - Ordena la primera columna en orden descendente.
 * - Establece la longitud de página por defecto a 5 y proporciona opciones de 5, 10, 15 y 20 registros.
 * - Configura la estructura del DOM para incluir botones y el filtro de búsqueda.
 * - Añade un botón para exportar los datos a un archivo de Excel.
 * - Permite recuperar una tabla existente en lugar de crear una nueva.
 * - Configura columnas fijas y opciones de desplazamiento horizontal y vertical.
 * 
 * Además, extiende la función de búsqueda de DataTables para incluir filtrado por fechas.
 * Utiliza moment.js para manejar y comparar fechas.
 * 
 * Asigna un evento click al botón de "filtrar por fechas" para aplicar el filtro de fechas y redibujar la tabla.
 * 
 */
$(document).ready(function () {
    let table = $('#tabla-permisos').DataTable({
        "order": [[ 0, 'desc' ]],
        "pageLength" : 5,
        "lengthMenu" : [5,10,15,20],
        "dom": '<"top"<"left-col"B><"right-col"f>>rtip',
        "buttons": [
            {
                extend: "excelHtml5",
                text: '<i class="fas fa-file-excel"></i>',
                titleAttr: "Exportar a Excel",
                className: "btn btn-success",
            },
        ],
        "retrieve": true,
        fixedColumns: true,
        scrollCollapse: true,
        scrollX: true,
        scrollY: 450
    });

    $.fn.dataTable.ext.search.push(
        function(settings, data, dataIndex) {
            let min = moment($('#fecha-inicio').val(), 'YYYY-MM-DD');
            let max = moment($('#fecha-fin').val(), 'YYYY-MM-DD');
            let createdAt = moment(data[0], 'YYYY-MM-DD');

            if (
                (!min.isValid() && !max.isValid()) ||
                (!min.isValid() && createdAt.isSameOrBefore(max)) ||
                (min.isSameOrBefore(createdAt) && !max.isValid()) ||
                (min.isSameOrBefore(createdAt) && createdAt.isSameOrBefore(max))
            ) {
                return true;
            }
            return false;
        }
    );

    $("#filtrar-por-fechas").click(function() {
        table.draw();
    });
});

/**
 * Este script maneja la obtención y filtrado de áreas para actualizar una tabla de permisos.
 * 
 * Funcionalidades incluidas:
 * - Realizar una petición AJAX para obtener las áreas disponibles y llenar un elemento <select> con ellas.
 * - Manejar el evento de clic en el botón de selección de área para filtrar y actualizar la tabla de permisos.
 * - Función para actualizar la tabla de permisos basada en el área seleccionada, realizando una petición fetch y
 * actualizando el contenido de la tabla con los datos recibidos.
 * 
 */
$(document).ready(function() {
    $.ajax({
        url: '/get_areas/',
        method: 'GET',
        success: function(data) {
            var selectArea = $('#selectAreaPermisos');
            selectArea.append(new Option('Todos', 'all'));
            data.forEach(function(area) {
                selectArea.append(new Option(area.name, area.id));
            });
        },
        error: function(error) {
            console.log("Error al obtener las áreas: ", error);
        }
    });

    // Manejar el botón de filtrado
    $('#selectAreaPermisos').click(function() {
        var areaId = $(this).val();
        updateTableByArea(areaId);
    });

    /**
     * Función que permite actualizar la tabla de visualizar permisos
     * a partir del área seleccionada en el botón select.
     * 
     * @param {int} areaId Recibe el ID del área seleccionada en el botón select.
     */
    async function updateTableByArea(areaId) {
        try {
            const response = await fetch(`/actualizar_tabla_areas/${areaId}/`);
            const data = await response.json();

            if (data.permisos) {
                var tbody = $('#tabla-permisos tbody');
                tbody.empty();

                data.permisos.forEach(function(permiso) {
                    var row = `
                        <tr>
                            <td>${permiso.creado}</td>
                            <td>${permiso.nombre_completo}</td>
                            <td>${permiso.cedula}</td>
                            <td>${permiso.area}</td>
                            <td>${permiso.turno}</td>
                            <td>${permiso.fecha_permiso}</td>
                            <td>${permiso.fecha_fin_permiso}</td>
                            <td>${permiso.hora_salida}</td>
                            <td>${permiso.hora_llegada}</td>
                            <td>${permiso.motivo_permiso}</td>
                            <td>${permiso.nombre_coordinador}</td>
                            <td>${permiso.compensa_tiempo}</td>
                            <td>${permiso.datos_adjuntos}</td>
                            <td>${permiso.observacion}</td>
                            <td>${permiso.creado_por}</td>
                            <td>${permiso.verificacion}</td>
                            <td>${permiso.estado}</td>
                            <td>${permiso.verificado_por}</td>
                            <td>${permiso.fecha_verificacion}</td>
                            <td>
                                <a type="button" href="${permiso.edit_url}" class="btn btn-success"><i class="bi bi-pencil"></i></a>
                            </td>
                        </tr>
                    `;
                    tbody.append(row);
                });
            } else {
                console.error("No se encontraron permisos");
            }
        } catch (error) {
            console.error("Error al actualizar la tabla", error);
        }
    }
});
// FIN TABLA VER PERMISOS

/**
 * TABLA VER LICENCIAS
 * 
 * Inicializa una tabla con DataTables y configura varias opciones:
 * - Ordena la primera columna en orden descendente.
 * - Establece la longitud de la pagina por defecto a 5 y proporciona opciones de 5, 10, 15 y 20 registros.
 * - Configura la estructura del DOM para incluir los botones y el filtro de búsqueda.
 * - Añade un botón para exportar los datos a un archivo de Excel.
 * - Permite recuperar una tabla existente en lugar de crear una nueva.
 * - Configura columnas fijas y opciones de desplazamiento horizontal y vertical.
 * 
 * Además, extiende la función de búsqueda de DataTables para incluir filtrado por fechas.
 * Utiliza moment.js para manejar y comparar fechas.
 * 
 * Asigna un evento click al botón de "filtrar por fechas" para aplicar el filtro de fechas y redibujar la tabla.
 *  
*/
$(document).ready(function () {
    let table = $('#tabla-licencias').DataTable({
        "order": [[ 0, 'desc' ]],
        "pageLength" : 5,
        "lengthMenu" : [5,10,15,20],
        "dom": '<"top"<"left-col"B><"right-col"f>>rtip',
        "buttons": [
            {
                extend: "excelHtml5",
                text: '<i class="fas fa-file-excel"></i>',
                titleAttr: "Exportar a Excel",
                className: "btn btn-success",
            },
        ],
        "retrieve": true,
        fixedColumns: true,
        scrollCollapse: true,
        scrollX: true,
        scrollY: 450
    });

    $.fn.dataTable.ext.search.push(
        function(settings, data, dataIndex) {
            let min = moment($('#fecha-inicio').val(), 'YYYY-MM-DD');
            let max = moment($('#fecha-fin').val(), 'YYYY-MM-DD');
            let createdAt = moment(data[0], 'YYYY-MM-DD');

            if (
                (!min.isValid() && !max.isValid()) ||
                (!min.isValid() && createdAt.isSameOrBefore(max)) ||
                (min.isSameOrBefore(createdAt) && !max.isValid()) ||
                (min.isSameOrBefore(createdAt) && createdAt.isSameOrBefore(max))
            ) {
                return true;
            }
            return false;
        }
    );

    $("#filtrar-por-fechas").click(function() {
        table.draw();
    });
});

/**
* Este script maneja la obtención y filtrado de áreas para actualizar una tabla de licencias.
* 
* Funcionalidades incluidas:
* - Realizar una petición AJAX para obtener las áreas disponibles y llenar un elemento <select> con ellas.
* - Manejar el evento de clic en el botón de selección de área para filtrar y actualizar la tabla de licencias.
* - Función para actualizar la tabla de licencias basada en el área seleccionada, realizando una petición fetch y
* actualizando el contenido de la tabla con los datos recibidos.
*/
$(document).ready(function() {
    $.ajax({
        url: '/get_areas/',
        method: 'GET',
        success: function(data) {
            var selectArea = $('#selectAreaLicencias');
            selectArea.append(new Option('Todos', 'all'));
            data.forEach(function(area) {
                selectArea.append(new Option(area.name, area.id));
            });
        },
        error: function(error) {
            console.log("Error al obtener las áreas: ", error);
        }
    });

    // Manejar el botón de filtrado
    $('#selectAreaLicencias').click(function() {
        var areaId = $(this).val();
        updateTableByArea(areaId);
    });

    /**
     * Función que permite actualizar la tabla de visualizar licencias
     * a partir del área seleccionada en el botón select.
     * 
     * @param {int} areaId Recibe el ID del área seleccionada en el botón select.
     */
    async function updateTableByArea(areaId) {
        try {
            const response = await fetch(`/actualizar_tabla_licencias_areas/${areaId}/`);
            const data = await response.json();

            if (data.licencias) {
                var tbody = $('#tabla-licencias tbody');
                tbody.empty();

                data.licencias.forEach(function(licencia) {
                    var row = `
                        <tr>
                            <td>${licencia.creado}</td>
                            <td>${licencia.nombre_completo}</td>
                            <td>${licencia.cedula}</td>
                            <td>${licencia.empresa}</td>
                            <td>${licencia.area}</td>
                            <td>${licencia.fecha_inicio}</td>
                            <td>${licencia.fecha_fin}</td>
                            <td>${licencia.tipo_licencia}</td>
                            <td>${licencia.motivo_licencia}</td>
                            <td>${licencia.observacion_licencia}</td>
                            <td>${licencia.nombre_coordinador}</td>
                            <td>${licencia.datos_adjuntos_licencias}</td>
                            <td>${licencia.creada_por}</td>
                            <td>${licencia.verificacion_licencia}</td>
                            <td>${licencia.estado_licencia}</td>
                            <td>${licencia.verificada_por}</td>
                            <td>${licencia.aprobacion_rrhh}</td>
                            <td>${licencia.observacion_rrhh}</td>
                            <td>${licencia.verificacion_rrhh}</td>
                            <td>${licencia.fecha_verificacion}</td>
                            <td>${licencia.fecha_aprobacion}</td>
                            <td>
                                <a type="button" href="${licencia.edit_url}" class="btn btn-success"><i class="bi bi-pencil"></i></a>
                            </td>
                        </tr>
                    `;
                    tbody.append(row);
                });
            } else {
                console.error("No se encontraron permisos");
            }
        } catch (error) {
            console.error("Error al actualizar la tabla", error);
        }
    }
});
// FIN TABLA VER LICENCIAS

/**
 * Este script permite la edición en línea de celdas en una tabla y guarda los cambios en el servidor.
 * 
 * Funcionalidades incluidas:
 * - Al hacer doble clic en una celda editable, se convierte en un campo de entrada de texto.
 * - Al perder el foco o presionar Enter en el campo de entrada, se guarda el nuevo valor en la celda 
 * y se envía al servidor.
 * - La función SendToServer maneja el envío de los datos modificados al servidor mediante una petición AJAX.
 * 
 */
$(document).ready(function () {
    $(document).on("dblclick", ".editable", function () {
        var value = $(this).text();
        var input = "<input type='text' class='input-data' value='" + value + "' class='form-control'>";
        $(this).html(input);
        $(this).removeClass("editable");
    });

    $(document).on("blur", ".input-data", function () {
        var value = $(this).val();
        var td = $(this).parent("td");
        $(this).remove();
        td.html(value);
        td.addClass("editable");
        var type = td.data("type");
        sendToServer(td.data("id"), value, type);
    });

    $(document).on("keypress", ".input-data", function (e) {
        var key = e.which;
        if (key == 13) {
            var value = $(this).val();
            var td = $(this).parent("td");
            $(this).remove();
            td.html(value);
            td.addClass("editable");
            var type = td.data("type");
            sendToServer(td.data("id"), value, type);
        }
    });

    /**
     * Función que envía los datos modificados al servidor mediante una petición AJAX.
     * 
     * @param {int} id - El ID del permiso.
     * @param {string} value - El nuevo valor de la celda.
     * @param {string} type - El tipo de dato que se está modificando.
     */
    function sendToServer(id, value, type, td) {
        console.log(id);
        console.log(value);
        console.log(type);
        var type = td.attr("data-type");
        console.log(type);
        $.ajax({
            url: "http://127.0.0.1:8000/save_permiso",
            type: "POST",
            data: { id: id, type: type, value: value },
        })
            .done(function (response) {
                console.log(response);
            })
            .fail(function () {
                console.log("ERROR OCURRED")
            });
    }
});
//Fin editar permisos