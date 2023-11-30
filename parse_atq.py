import asyncio
from datetime import datetime
from sqlmodel import SQLModel
from dataclasses import dataclass
from database import Job


async def parse_atq():
    proc = await asyncio.create_subprocess_shell("atq", stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    joblist = [nn.strip() for nn in stdout.decode('utf-8').split("\n") if nn.strip()]
    retval = []
    for jl in joblist:
        job_id, rest = jl.split('\t')
        *time, _, _ = rest.split(' ')
        time = ' '.join(time)
        timestamp = datetime.strptime(time, "%a %b %d %H:%M:%S %Y") 
        retval.append((job_id, timestamp))
    proc = await asyncio.create_subprocess_shell("""atq | awk '{ system("at -c " $1) }'""", stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    job_details = [nn.strip() for nn in stdout.decode('utf-8').split("\n\n") if nn.strip()][:-1]
    retval2 = []
    for jd in job_details:
        jdend = jd.split('\n')[-1]
        _,_,phone_number,rejects = jdend.split(' ')
        retval2.append((phone_number, rejects))
    retval3 = []
    for (job_id, timestamp), (phone_number, rejects) in zip(retval, retval2):
        retval3.append(Job(job_id=job_id, timestamp=timestamp, phone_number=phone_number, rejects=int(rejects)))
    retval3.sort(key = lambda x: x.timestamp)
    return retval3


    

