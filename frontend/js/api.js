const API_URL = "http://127.0.0.1:8000";

window.apiGet = async function (ruta) {
  const respuesta = await fetch(`${API_URL}${ruta}`);

  let resultado = null;

  try {
    resultado = await respuesta.json();
  } catch {
    resultado = null;
  }

  if (!respuesta.ok) {
    throw new Error(
      resultado?.detail || `Error HTTP ${respuesta.status} al consultar ${ruta}`
    );
  }

  return resultado;
};

window.apiPost = async function (ruta, datos) {
  const respuesta = await fetch(`${API_URL}${ruta}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(datos)
  });

  let resultado = null;

  try {
    resultado = await respuesta.json();
  } catch {
    resultado = null;
  }

  if (!respuesta.ok) {
    throw new Error(
      resultado?.detail || `Error HTTP ${respuesta.status} al enviar datos a ${ruta}`
    );
  }

  return resultado;
};

window.apiPut = async function (ruta, datos) {
  const respuesta = await fetch(`${API_URL}${ruta}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(datos)
  });

  let resultado = null;

  try {
    resultado = await respuesta.json();
  } catch {
    resultado = null;
  }

  if (!respuesta.ok) {
    throw new Error(
      resultado?.detail || `Error HTTP ${respuesta.status} al actualizar ${ruta}`
    );
  }

  return resultado;
};

window.apiDelete = async function (ruta) {
  const respuesta = await fetch(`${API_URL}${ruta}`, {
    method: "DELETE"
  });

  let resultado = null;

  try {
    resultado = await respuesta.json();
  } catch {
    resultado = null;
  }

  if (!respuesta.ok) {
    throw new Error(
      resultado?.detail || `Error HTTP ${respuesta.status} al eliminar ${ruta}`
    );
  }

  return resultado;
};
window.apiPatch = async function (ruta, datos = null) {
  const opciones = {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json"
    }
  };

  if (datos !== null) {
    opciones.body = JSON.stringify(datos);
  }

  const respuesta = await fetch(`${API_URL}${ruta}`, opciones);

  let resultado = null;

  try {
    resultado = await respuesta.json();
  } catch {
    resultado = null;
  }

  if (!respuesta.ok) {
    throw new Error(
      resultado?.detail || `Error HTTP ${respuesta.status} al modificar ${ruta}`
    );
  }

  return resultado;
};