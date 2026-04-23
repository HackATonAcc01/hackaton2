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

const card1 = document.querySelector('#card1');
card1.addEventListener('click', function(event) {
    window.location.href = "/route/1"
});

const card2 = document.querySelector('#card2');
card2.addEventListener('click', function(event) {
    window.location.href = "/route/2"
});

const card3 = document.querySelector('#card3');
card3.addEventListener('click', function(event) {
    window.location.href = "/route/3"
});

const card4 = document.querySelector('#card4');
card4.addEventListener('click', function(event) {
    window.location.href = "/route/4"
});

const card5 = document.querySelector('#card5');
card5.addEventListener('click', function(event) {
    window.location.href = "/route/5"
});

const card6 = document.querySelector('#card6');
card6.addEventListener('click', function(event) {
    window.location.href = "/route/6"
});

function getCookie(name) {
  let cookie = document.cookie.split('; ').find(row => row.startsWith(name + '='));
  return cookie ? cookie.split('=')[1] : null;
}
