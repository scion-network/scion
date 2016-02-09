""" Ingestion plugin. """

__author__ = 'Michael Meisinger'

from ion.processes.data.ingest.ingestion_process import IngestionPlugin
from pyon.public import log, StandaloneProcess, BadRequest, CFG, StreamSubscriber, PRED, RT

from interface.objects import StreamRoute, DataPacket, Instrument


class ScionIngestionPlugin(IngestionPlugin):

    def on_init(self):
        self.ds_cache = {}

    def get_dataset_info(self, packet):
        resource_id = packet.resource_id
        if resource_id in self.ds_cache:
            return self.ds_cache[resource_id]

        inst_obj = self.rr.read(resource_id)

        if not isinstance(inst_obj, Instrument):
            raise BadRequest("Unknown resource type: %s" % inst_obj.type_)

        dataset_objs, _ = self.rr.find_objects(resource_id, PRED.hasDataset, RT.Dataset, id_only=False)
        if not dataset_objs:
            raise BadRequest("Could not find dataset")
        dataset_obj = dataset_objs[0]

        ds_info = dict(dataset_id=dataset_obj._id, schema=dataset_obj.schema_definition)
        self.ds_cache[resource_id] = ds_info

        return ds_info