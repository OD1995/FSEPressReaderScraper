import logging
from ..MyFunctions import update_row_status
import azure.durable_functions as df
import azure.functions as func
import json

async def main(req: func.HttpRequest, starter: str) -> func.HttpResponse:
    client = df.DurableOrchestrationClient(starter)
    instance_id = await client.start_new(
        orchestration_function_name="Orchestrator",
        instance_id=None,
        client_input={
            a:req.params.get(a)
            for a in ['publicationCID','publishedDate']
        }
    )

    logging.info(f"Started orchestration with ID = '{instance_id}'.")

    csr = client.create_check_status_response(req, instance_id)
    A = json.loads(csr.get_body())
    logging.info(A.get("statusQueryGetUri"))
    ## Set StatusQueryGetUri value in SQL
    update_row_status(
        publicationCID=req.params.get("publicationCID"),
        publishedDate=req.params.get("publishedDate"),
        uri=A.get("statusQueryGetUri")
    )
    
    return csr
