# This function an HTTP starter function for Durable Functions.
# Before running this sample, please:
# - create a Durable orchestration function
# - create a Durable activity function (default name is "Hello")
# - add azure-functions-durable to requirements.txt
# - run pip install -r requirements.txt
 
import logging
from MyFunctions import update_row_status
import azure.functions as func
import azure.durable_functions as df


async def main(req: func.HttpRequest, starter: str) -> func.HttpResponse:
    client = df.DurableOrchestrationClient(starter)
    # instance_id = await client.start_new(req.route_params["functionName"], None, None)
    instance_id = await client.start_new(
        orchestration_function_name=req.route_params["functionName"],
        instance_id=None,
        client_input={
            a:req.params.get(a)
            for a in ['publicationCID','publicationDate']
        }
    )

    logging.info(f"Started orchestration with ID = '{instance_id}'.")

    csr = client.create_check_status_response(req, instance_id)
    ## Set StatusQueryGetUri value in SQL
    update_row_status(
        publicationCID=req.params.get("publicationCID"),
        publishedDate=req.params.get("publishedDate"),
        uri=csr["statusQueryGetUri"]
    )
    
    return "done"