window.onload = function() {
    let cookies = document.cookie;

    if (!(cookies && getCookie("login_"))){
        document.getElementById('options').id = "guest";
        let elem1 = document.createElement("a");
        elem1.href = "/login";
        elem1.innerText = "войти";
        elem1.id = "login"
        let pl = document.getElementById('profilelabel');
        pl.innerText= "";
        pl.appendChild(elem1);
    }else{
        try{
            document.getElementById('guest').id = "options";
        }catch (exceptionVar){
            //pass
        }
        let pl = document.getElementById('profilelabel');
        pl.innerHTML = "";
        pl.innerText = getCookie("login_");
        let options = document.getElementById('options');
        options.style.right = (getCookie("login_").length * 20 / 3).toString() + "px";
    }


};

function getCookie(name) {
  let cookie = document.cookie.split('; ').find(row => row.startsWith(name + '='));
  return cookie ? cookie.split('=')[1] : null;
}
