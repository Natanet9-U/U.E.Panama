import "./Login.css";
 // login component
function Login() {
  return (
    <div className="container">
 
      <div className="card">
 
        <h1 className="title">SISTEMA ACADÉMICO</h1>
 
        <p className="subtitle">
          INICIA SESIÓN PARA CONTINUAR
        </p>
 
        <form className="form">
 
          <div className="input-group">
            <label>CORREO ELECTRONICO</label>
            <input
              type="email"
              placeholder="Ingrese su correo"
            />
          </div>
 
          <div className="input-group">
            <label>CONTRASEÑA</label>
            <input
              type="password"
              placeholder="Ingrese su contraseña"
            />
          </div>
 
          <a href="#" className="link">
            ¿OLVIDO SU CONTRASEÑA?
          </a>
 
          <button>
            INICIAR SESIÓN
          </button>
 
        </form>
 
      </div>
 
    </div>
  );
}
 
export default Login;
