// Simple goal: Create buttons that send POST requests without
// refreshing the page.

let teleop_btns = document.getElementsByClassName('teleop');

for(const button of teleop_btns){
    button.addEventListener('click', (e) =>{
        e.preventDefault()
        let xhr = new XMLHttpRequest();
        xhr.open("POST", "/", true);
        xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        xhr.onreadystatechange = () =>{
            if(xhr.readyState === 4 && xhr.status === 200){
                console.log(xhr.responseText);
            }
        };
        xhr.send("cmd="+button.name+"\0") // use cmd as the key to make it easier to forward. Append EOF character we are using in our Robot Server.s
    });
}

var intervalId = setInterval(function(){
    xhttp = new XMLHttpRequest()
    xhttp.open("GET", "/sensor", true)
    xhttp.onload = function(){
        let data = xhttp.responseText
        let parser = new DOMParser()
        let xmlDoc = parser.parseFromString(data, 'text/xml')
        let message_node = xmlDoc.querySelector('message')
        smoke_vals = message_node.textContent.replace(/b'|'/g, '');
        smoke_div = document.getElementById("smoke")

        smoke_div.innerHTML = smoke_vals
        
    }
    xhttp.send()
}, 3000);