from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.applications import Starlette
from . import grade


app = Starlette()


@app.route('/grade-animal-test')
async def grade_animal_test(request):
    return JSONResponse(grade.grade_animal_test(await request.json()))


@app.route('/grade-l-test')
async def grade_l_test(request):
    return JSONResponse(grade.grade_l_test(await request.json()))


@app.route('/grade-memory-test')
async def grade_memory_test(request):
    json = await request.json()
    transcript = json['transcript']
    word_list = json['word_list']
    return JSONResponse(grade.grade_memory_test(transcript, word_list))
