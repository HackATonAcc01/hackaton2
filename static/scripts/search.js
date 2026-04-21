

document.addEventListener('keydown', function(event) {
    const input = document.getElementById('input');
    if (event.key.length != 1) return;
    fetch("/search", {
        method: "POST",
        body: JSON.stringify({
            typed: input.value
        }),
        headers: {
            "Content-type": "application/json; charset=UTF-8"
        }
    }).then(response => {
    return response.json();
    }).then(jsonResponse => {
        const parent = document.getElementById('res');
        parent.innerHTML = '';
        for(let i of jsonResponse["games"]){
            let elem = document.createElement("h4");
            let elem1 = document.createElement("a");
            elem1.innerText = i;
            elem1.href = "/game/" + i;
            elem.appendChild(elem1);
            parent.appendChild(elem);
        }
    }).catch (error => {
        console.log(error)
    });
});