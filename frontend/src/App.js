import axios from "axios";
import { useEffect } from "react";

function App() {
  useEffect(() => {
    axios.get("http://127.0.0.1:8000/api/")
      .then(res => console.log(res.data))
      .catch(err => console.error(err));
  }, []);

  return <h1>React funcionando</h1>;
}

export default App;