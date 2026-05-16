from __future__ import annotations

import argparse
import os
from datetime import datetime
from pathlib import Path
from typing import Dict

import pandas as pd
import requests
from dotenv import load_dotenv


def fetch_kosis_data(
    api_key: str,
    region: str,
    start_period: str,
    end_period: str,
    industry_code: str,
) -> pd.DataFrame:
    """KOSIS 예시 조회 후 데이터프레임으로 변환한다."""
    url = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
    params = {
        "method": "getList",
        "apiKey": api_key,
        "format": "json",
        "jsonVD": "Y",
        "prdSe": "M",
        "startPrdDe": start_period,
        "endPrdDe": end_period,
        "orgId": "101",
        "tblId": "DT_1B040A3",
        "itmId": industry_code,
        "objL1": region,
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    df = pd.DataFrame(data)
    df["source"] = "kosis"
    return df


def fetch_customs_data(
    api_key: str,
    region: str,
    start_period: str,
    end_period: str,
    hs_code: str,
) -> pd.DataFrame:
    """관세청(관세무역개발원 OpenAPI 프록시) 예시 조회 후 데이터프레임으로 변환한다."""
    url = "https://apis.data.go.kr/1220000/Newtrade/getNewtradeList"
    params = {
        "serviceKey": api_key,
        "resultType": "json",
        "strtYymm": start_period,
        "endYymm": end_period,
        "hsSgn": hs_code,
        "prcCnt": "100",
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    payload = response.json()
    items = (
        payload.get("response", {})
        .get("body", {})
        .get("items", {})
        .get("item", [])
    )

    if isinstance(items, dict):
        items = [items]

    df = pd.DataFrame(items)
    df["region"] = region
    df["source"] = "customs"
    return df


def build_output_stem(prefix: str = "pohang_battery_industry") -> str:
    today = datetime.now().strftime("%Y%m%d")
    return f"{prefix}_{today}"


def ensure_output_dir(path: str = "output") -> Path:
    output_dir = Path(path)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def write_csv_xlsx(df: pd.DataFrame, csv_path: Path, xlsx_path: Path) -> None:
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    df.to_excel(xlsx_path, index=False)


def save_dataframes(
    output_dir: Path,
    output_stem: str,
    save_mode: str,
    kosis_df: pd.DataFrame,
    customs_df: pd.DataFrame,
) -> Dict[str, Path]:
    saved_files: Dict[str, Path] = {}

    if save_mode in {"separate", "both"}:
        kosis_csv = output_dir / f"{output_stem}_kosis.csv"
        kosis_xlsx = output_dir / f"{output_stem}_kosis.xlsx"
        write_csv_xlsx(kosis_df, kosis_csv, kosis_xlsx)
        saved_files["kosis_csv"] = kosis_csv
        saved_files["kosis_xlsx"] = kosis_xlsx

        customs_csv = output_dir / f"{output_stem}_customs.csv"
        customs_xlsx = output_dir / f"{output_stem}_customs.xlsx"
        write_csv_xlsx(customs_df, customs_csv, customs_xlsx)
        saved_files["customs_csv"] = customs_csv
        saved_files["customs_xlsx"] = customs_xlsx

    if save_mode in {"merged", "both"}:
        merged_df = pd.concat([kosis_df, customs_df], ignore_index=True, sort=False)
        merged_csv = output_dir / f"{output_stem}.csv"
        merged_xlsx = output_dir / f"{output_stem}.xlsx"
        write_csv_xlsx(merged_df, merged_csv, merged_xlsx)
        saved_files["merged_csv"] = merged_csv
        saved_files["merged_xlsx"] = merged_xlsx

    return saved_files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="KOSIS/관세청 데이터를 조회하고 CSV/XLSX 산출물을 생성합니다."
    )
    parser.add_argument("--region", required=True, help="지역 코드 (예: 37010)")
    parser.add_argument("--start-period", required=True, help="시작 기간 (YYYYMM)")
    parser.add_argument("--end-period", required=True, help="종료 기간 (YYYYMM)")
    parser.add_argument("--industry-code", required=True, help="산업 코드")
    parser.add_argument("--hs-code", required=True, help="HS 코드")
    parser.add_argument(
        "--save-mode",
        choices=["separate", "merged", "both"],
        default="both",
        help="산출물 저장 방식",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()

    kosis_api_key = os.getenv("KOSIS_API_KEY")
    customs_api_key = os.getenv("CUSTOMS_API_KEY")

    if not kosis_api_key:
        raise ValueError("환경변수 KOSIS_API_KEY가 설정되어 있지 않습니다.")
    if not customs_api_key:
        raise ValueError("환경변수 CUSTOMS_API_KEY가 설정되어 있지 않습니다.")

    kosis_df = fetch_kosis_data(
        api_key=kosis_api_key,
        region=args.region,
        start_period=args.start_period,
        end_period=args.end_period,
        industry_code=args.industry_code,
    )

    customs_df = fetch_customs_data(
        api_key=customs_api_key,
        region=args.region,
        start_period=args.start_period,
        end_period=args.end_period,
        hs_code=args.hs_code,
    )

    output_stem = build_output_stem()
    output_dir = ensure_output_dir("output")

    saved_files = save_dataframes(
        output_dir=output_dir,
        output_stem=output_stem,
        save_mode=args.save_mode,
        kosis_df=kosis_df,
        customs_df=customs_df,
    )

    print("저장 완료:")
    for name, file_path in saved_files.items():
        print(f"- {name}: {file_path}")


if __name__ == "__main__":
    main()
