const assert = require('assert');
const fs = require('fs');
const http = require('http');
const path = require('path');
const { spawn } = require('child_process');

const projectRoot = path.resolve(__dirname, '..');
const logPath = path.join(projectRoot, 'test-results.log');
const port = 3000;
const ADMIN_KEY = process.env.ADMIN_API_KEY || 'dev-admin-key-change-me';

fs.writeFileSync(logPath, '', 'utf8');

function writeResult(method, endpoint, expectedStatus, receivedStatus, passed) {
    fs.appendFileSync(
        logPath,
        `${new Date().toISOString()} TESTE ${method} ${endpoint} | esperado=${expectedStatus} recebido=${receivedStatus} | ${passed ? 'SUCESSO' : 'FALHA'}\n`,
        'utf8'
    );
}

function request(method, endpoint, body, extraHeaders) {
    return new Promise((resolve, reject) => {
        const payload = body ? JSON.stringify(body) : null;
        const headers = Object.assign(
            {},
            payload ? { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(payload) } : {},
            extraHeaders || {}
        );
        const req = http.request({
            hostname: '127.0.0.1',
            port,
            path: endpoint,
            method,
            headers
        }, (res) => {
            let responseBody = '';
            res.setEncoding('utf8');
            res.on('data', (chunk) => { responseBody += chunk; });
            res.on('end', () => resolve({ status: res.statusCode, body: responseBody }));
        });
        req.on('error', reject);
        if (payload) req.write(payload);
        req.end();
    });
}

async function testEndpoint(method, endpoint, expectedStatus, body, assertion, extraHeaders) {
    let response;
    try {
        response = await request(method, endpoint, body, extraHeaders);
        const passed = response.status === expectedStatus;
        writeResult(method, endpoint, expectedStatus, response.status, passed);
        assert.strictEqual(response.status, expectedStatus, response.body);
        if (assertion) assertion(response.body);
    } catch (error) {
        if (!response) {
            writeResult(method, endpoint, expectedStatus, 'ERRO', false);
        }
        throw error;
    }
}

function waitForServer(serverProcess) {
    return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => reject(new Error('Servidor não iniciou a tempo')), 5000);
        serverProcess.stdout.on('data', (chunk) => {
            if (chunk.toString().includes('porta 3000')) {
                clearTimeout(timeout);
                resolve();
            }
        });
        serverProcess.on('error', reject);
        serverProcess.on('exit', (code) => {
            if (code !== null) reject(new Error(`Servidor encerrou antes dos testes: ${code}`));
        });
    });
}

async function run() {
    const server = spawn(process.execPath, ['src/app.js'], {
        cwd: projectRoot
    });

    try {
        await waitForServer(server);

        await testEndpoint('POST', '/api/checkout', 200, {
            usr: 'Guilherme',
            eml: 'gui@fullcycle.com.br',
            pwd: 'senhaforte',
            c_id: 2,
            card: '4111222233334444'
        }, (body) => {
            assert.match(body, /"msg":"Sucesso"/);
        });

        await testEndpoint('POST', '/api/checkout', 400, {
            usr: 'João',
            eml: 'joao@teste.com',
            pwd: '123',
            c_id: 1,
            card: '5111222233334444'
        }, (body) => {
            assert.deepStrictEqual(JSON.parse(body), { erro: 'Pagamento recusado' });
        });

        // Endpoints administrativos agora exigem a chave X-Admin-Key.
        await testEndpoint('GET', '/api/admin/financial-report', 401, null, (body) => {
            assert.match(body, /Chave de administrador/);
        });

        await testEndpoint('GET', '/api/admin/financial-report', 200, null, (body) => {
            const report = JSON.parse(body);
            assert.strictEqual(report.length, 2);
            assert.ok(report.some((course) => course.course === 'Docker'));
        }, { 'X-Admin-Key': ADMIN_KEY });

        await testEndpoint('DELETE', '/api/users/1', 401, null, null);

        await testEndpoint('DELETE', '/api/users/1', 200, null, (body) => {
            const parsed = JSON.parse(body);
            assert.match(parsed.mensagem, /removido com sucesso/);
        }, { 'X-Admin-Key': ADMIN_KEY });
    } finally {
        server.kill();
    }
}

run()
    .then(() => {
        console.log('7 testes de endpoints concluídos com sucesso.');
    })
    .catch((error) => {
        console.error(`Falha nos testes: ${error.message}`);
        process.exitCode = 1;
    });
