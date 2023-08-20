"""axolotl.data.seq

Contain classes definition for sequence's DataFrames.
"""

from pyspark.sql import DataFrame, Row, types
from pyspark.sql import SparkSession
from abc import abstractmethod

from axolotl.core import ioDF
from typing import Dict


class SeqDF(ioDF):
    """basic sequence dataframe (abstract class)"""
    
    @classmethod
    def _getSchemaSpecific(cls) -> types.StructType:
        return types.StructType([
            types.StructField('seq_id', types.StringType()),
            types.StructField('desc', types.StringType()),
            types.StructField('sequence', types.StringType()),
            types.StructField('length', types.LongType())
        ])
    
    @classmethod
    @abstractmethod
    def getAllowedLetters(cls) -> str:
        raise NotImplementedError("calling an unimplemented abstract method getAllowedLetters()")
        
    @classmethod
    @abstractmethod
    def validateRowSpecific(cls, row: Row) -> bool:
        raise NotImplementedError("calling an unimplemented abstract method validateRowSpecific()")
        
    @classmethod
    def validateRow(cls, row: Row) -> bool:
        allowed_letters = cls.getAllowedLetters()
        return (
            all(c in allowed_letters for c in row["sequence"]) and
            len(row["sequence"]) == row["length"] and
            cls.validateRowSpecific(row)
        )


class NuclSeqDF(SeqDF):
    """basic sequence dataframe (abstract class)"""
    
    @classmethod
    def _getSchemaSpecific(cls) -> types.StructType:
        return SeqDF ._getSchemaSpecific()

    @classmethod
    def getAllowedLetters(cls) -> str:
        return "ATGCNatgcn"

    @classmethod
    def validateRowSpecific(cls, row: Row) -> bool:
        return True

    @classmethod
    def fetch_seq(cls, seq:str, loc:Dict):
        reverse = loc.strand == -1
        if reverse:
            convert = {
            "A": "T", "T": "A", "G": "C", "C": "G",
            "a": "t", "t": "a", "g": "c", "c": "g"
            }
            snippet = "".join([convert.get(c, c) for c in seq[loc.end-1:loc.start-2:-1]])
        else:
            snippet = seq[loc.start-1:loc.end]
        return snippet


class ProtSeqDF(SeqDF):
    
    @classmethod
    def _getSchemaSpecific(cls) -> types.StructType:
        return SeqDF._getSchemaSpecific()

    @classmethod
    def getAllowedLetters(cls) -> str:
        return "ABCDEFGHIJKLMNOPQRSTUVWYZX*-abcdefghijklmnopqrstuvwyzx"
    
    @classmethod
    def validateRowSpecific(cls, row: Row) -> bool:
        return True


class ReadSeqDF(NuclSeqDF):
    
    @classmethod
    def _getSchemaSpecific(cls) -> types.StructType:
        return SeqDF._getSchemaSpecific()\
            .add(types.StructField("quality_scores", types.ArrayType(types.ByteType())))

    @classmethod
    def validateRowSpecific(cls, row: Row) -> bool:
        return (
            len(row["quality_scores"]) == row["length"]
        )


class PReadSeqDF(ReadSeqDF):
    
    @classmethod
    def _getSchemaSpecific(cls) -> types.StructType:
        return ReadSeqDF._getSchemaSpecific()\
            .add(types.StructField("sequence_2", types.StringType()))\
            .add(types.StructField("length_2", types.LongType()))\
            .add(types.StructField("quality_scores_2", types.ArrayType(types.ByteType())))

    @classmethod
    def validateRowSpecific(cls, row: Row) -> bool:
        allowed_letters = cls.getAllowedLetters()
        return (
            ReadSequenceDF.validateRowSpecific(row) and
            all(c in allowed_letters for c in row["sequence_2"]) and
            len(row["sequence_2"]) == row["length_2"] and
            len(row["quality_scores_2"]) == row["length_2"]
        )