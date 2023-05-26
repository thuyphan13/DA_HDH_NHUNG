let lightOnNoti='Bạn có muốn bật đèn không?'
let lightOffNoti='Bạn có muốn tắt đèn không?'
let DoorOpenNoti='Bạn có muốn mở cửa không?'
let DoorCloseNoti='Bạn có muốn đóng cửa không?'
document.querySelector('#but1').addEventListener('click',()=> {
    if (confirm(lightOnNoti)){
        socket.emit('led', 'on')
        // document.getElementById("but1").style.background="blue"
        // document.getElementById("but2").style.background="gray"
        document.querySelector('#anh1').src='./img/den_bat.png'
        // document.getElementById('nutall').style.background= 'red'
    }
})
document.querySelector('#but2').addEventListener('click',()=> {
    if (confirm(lightOffNoti)){
        socket.emit('led', 'off')
        // document.getElementById("but2").style.background="blue"
        // document.getElementById("but1").style.background="gray"
        document.querySelector('#anh1').src='./img/den_tat.png'
    }
})
document.querySelector('input').onclick = function(e){
    if (this.checked){
        if (confirm(DoorOpenNoti)){
            socket.emit('door', 'on')
            document.querySelector('#anh2').src='./img/cua_mo.png'
            document.querySelector('input').checked= true
        }
        else{
            document.querySelector('input').checked= false
            document.querySelector('#anh2').src='./img/cua_dong.png'
        }
    }
    else{
        if (confirm(DoorCloseNoti)){
            socket.emit('door', 'off')
            document.querySelector('#anh2').src='./img/cua_dong.png'
            document.querySelector('input').checked= false
        }
        else{
            document.querySelector('input').checked= true
            document.querySelector('#anh2').src='./img/cua_mo.png'
        }
    }
}

//------Socket IO ----

const socket = io();

socket.on('updateSensor', msg => {     //lang nghe du lieu tu mqtt
    console.log(msg);
    handlingData(msg);
});

socket.on('led', msg => {
    if (msg === 'on') {
        document.querySelector('#anh1').src = './img/den_bat.png';
    }
    if (msg === 'off') {
        document.querySelector('#anh1').src = './img/den_tat.png';
    }
    console.log(`led ${msg}`);
});

socket.on('door', msg => {
    if (msg === 'on') {
        document.querySelector('#anh2').src = './img/cua_mo.png';
    }
    if (msg === 'off') {
        document.querySelector('#anh2').src = './img/cua_dong.png';
    }
    console.log(`door ${msg}`);
});