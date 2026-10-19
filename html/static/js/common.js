fetch('nav.html')
    .then(r => r.text())
    .then(t => {
        document.getElementById('nav').innerHTML = t;
        loadUserInfo();
    });

function loadUserInfo() {
    let use = new XMLHttpRequest();
    use.open('get', 'http://localhost:8000/myapp/user/info/');
    use.withCredentials = true;
    use.send();
    use.onreadystatechange = function () {
        if (use.readyState != 4) return;
        if (use.status == 200) {
            let res = JSON.parse(use.responseText);
            if (res.status != 200) {
                window.location.href = 'login.html';
                return;
            }
            window.userid = res.data['id'];
            window.username = res.data['username'];
            document.getElementById('user').innerText = window.username;

            let out = document.getElementById("logout")
            out.onclick = function() {
                let xml = new XMLHttpRequest();
                xml.open("GET", "http://localhost:8000/myapp/log/out/");
                xml.withCredentials = true;
                xml.onreadystatechange = function () {
                    if (xml.readyState != 4) return
                    if (xml.status == 200) {
                        window.location.href = "login.html"
                    } else {
                        alert("退出失败")
                    }
                }
                xml.send();
            }

            if (typeof onUserInfoReady == 'function') {
                onUserInfoReady();
            }
        }
    };
}
