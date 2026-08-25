const express = require('express');
const session = require('express-session');
const path = require('path');
require('dotenv').config();

const app = express();

app.use(session({
    secret: process.env.SESSION_SECRET || 'clave_secreta',
    resave: false,
    saveUninitialized: false,
    cookie: { secure: false } // Ponlo en true si despliegas en un servidor con HTTPS
}));

app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// Archivos públicos (Landing page abierta a todo el mundo)
app.use(express.static(path.join(__dirname, 'public')));

// Ruta de Login segura
app.post('/api/login', (req, res) => {
    const { usuario, password } = req.body;

    if (usuario === process.env.ADMIN_USER && password === process.env.ADMIN_PASS) {
        req.session.autenticado = true;
        req.session.rol = 'admin';
        return res.json({ success: true, redirect: '/admin-dashboard' });
    } else if (usuario === 'cliente' && password === 'cliente123') { // Aquí luego puedes conectar tu base de datos o Airtable
        req.session.autenticado = true;
        req.session.rol = 'cliente';
        return res.json({ success: true, redirect: '/client-dashboard' });
    }

    res.status(401).json({ success: false, message: 'Usuario o contraseña incorrectos' });
});

// Guardia de seguridad (Middleware)
function verificarSesion(req, res, next) {
    if (req.session && req.session.autenticado) {
        return next();
    }
    res.redirect('/');
}

// Rutas Privadas (Protegidas por el servidor)
app.get('/admin-dashboard', verificarSesion, (req, res) => {
    if (req.session.rol !== 'admin') return res.status(403).send('Acceso Prohibido');
    res.sendFile(path.join(__dirname, 'private', 'admin.html'));
});

app.get('/client-dashboard', verificarSesion, (req, res) => {
    if (req.session.rol !== 'cliente') return res.status(403).send('Acceso Prohibido');
    res.sendFile(path.join(__dirname, 'private', 'client.html'));
});

app.get('/logout', (req, res) => {
    req.session.destroy(() => {
        res.redirect('/');
    });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Servidor de Ingeniería MYP activo en http://localhost:${PORT}`);
});