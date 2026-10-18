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
            if (typeof onUserInfoReady == 'function') {
                onUserInfoReady();
            }
        }
    };
}
