const mqtt = require('mqtt')
const express = require('express')
const app = express()
const http = require('http')
const server = http.createServer(app)
const { Server } = require('socket.io')
const io = new Server(server)
app.use(express.static('public'));

const options = {
    port: 1883,
    host: 'broker.mqttdashboard.com',
    clientId: 'clientId-gAe5UTm3Ou',
    username: 'duc',
    password: '123456',
}
const client = mqtt.connect(options);
client.on('connect', () => {
    console.log('MQTT connected!!');
});
const sensors = 'sensorData'
const led = 'LED'
const door = 'DOOR'
client.subscribe(sensors, () => {
    client.on('message', (topic, message, packet) => {
        console.log(message.toString());
        io.sockets.emit('updateSensor', message.toString().split(' '))
        // insertTB(`'${topic}', ${message.toString().split(' ')}`);
    });
});
io.on('connection', socket => {
    console.log(`user ${socket.id} connected`)
});

io.on('connection', socket => {
    socket.on('led', msg => {
        io.sockets.emit('led', msg);
        msg === 'on' && client.publish(led, msg)
        msg === 'off' && client.publish(led, msg)
    });
    socket.on('door', msg => {
        io.sockets.emit('led2', msg);
        msg === 'on' && client.publish(cua, msg)
        msg === 'off' && client.publish(cua, msg)
    })
})

server.listen(3001, () => {
    console.log('listening on *:3001')
});

