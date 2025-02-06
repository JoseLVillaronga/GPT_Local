// Script para inyectar en la página de login de Teccam
(function() {
    // Verificar periódicamente si el usuario está logueado
    const checkLoginStatus = () => {
        fetch('/prod_0dd4b2cd-a527-4025-9a36-12ea922b3b84.php')
            .then(response => response.json())
            .then(data => {
                if (data && data.usuario) {
                    // Usuario logueado, notificar a la ventana padre
                    window.opener.postMessage('LOGIN_SUCCESS', '*');
                }
            })
            .catch(error => console.error('Error checking login status:', error));
    };

    // Verificar cada segundo
    setInterval(checkLoginStatus, 1000);
})();
