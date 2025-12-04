#!/usr/bin/env python3
"""
Complete refactoring: Move all sections under 'sections:' and add missing sections.
"""

import yaml
import sys

def complete_refactor(input_file, output_file):
    """Complete refactoring of rulebook."""
    
    # Read and parse original
    with open(input_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    if data is None:
        print("ERROR: Failed to parse YAML")
        return False
    
    # Build new structure
    new_data = {
        'version': data.get('version', '2.0'),
        'title': data.get('title', ''),
        'description': data.get('description', ''),
        'metadata': data.get('metadata', {}),
        'jurisdiction': data.get('jurisdiction', ''),
        'authority': data.get('authority', ''),
        'disclaimer': data.get('disclaimer', ''),
        'sections': {}
    }
    
    # Sections to move
    section_names = ['as_standards', 'ind_as_mappings', 'schedule_iii_engine', 
                     'gst_itc_engine', 'tds_tcs_engine']
    
    # Move sections
    for section_name in section_names:
        if section_name in data and data[section_name] is not None:
            new_data['sections'][section_name] = data[section_name]
    
    # If as_standards is None, try to reconstruct from root-level AS keys
    if 'as_standards' not in new_data['sections'] or new_data['sections']['as_standards'] is None:
        as_standards = {}
        as_keys = [k for k in data.keys() if k.startswith('AS') and k[2:].isdigit()]
        if as_keys:
            as_standards['meta'] = data.get('meta', {})
            for as_key in sorted(as_keys):
                as_standards[as_key] = data[as_key]
            new_data['sections']['as_standards'] = as_standards
    
    # Add ind_as_mappings if missing
    if 'ind_as_mappings' not in new_data['sections'] and 'ind_as_mappings' in data:
        new_data['sections']['ind_as_mappings'] = data['ind_as_mappings']
    
    # Add cashflow section
    as_standards = new_data['sections'].get('as_standards', {})
    if as_standards and isinstance(as_standards, dict):
        as3 = as_standards.get('AS3', {})
        if as3:
            new_data['sections']['cashflow'] = {
                'meta': {
                    'description': 'Cash Flow Statement classification rules based on AS3',
                    'source': 'AS3 - Cash Flow Statements'
                },
                'operating': {
                    'keywords': [
                        'sale', 'revenue', 'rent', 'receivables', 'payables',
                        'supplier', 'employee', 'salary', 'utility', 'tax', 'gst', 'tds'
                    ],
                    'examples': (as3.get('operating_examples', {}).get('cash_inflows', []) + 
                               as3.get('operating_examples', {}).get('cash_outflows', []))
                },
                'investing': {
                    'keywords': [
                        'purchase of machinery', 'ppe', 'capital expenditure',
                        'investment', 'loan advanced', 'loan recovered'
                    ],
                    'examples': as3.get('investing_examples', [])
                },
                'financing': {
                    'keywords': [
                        'loan from director', 'interest paid', 'share capital raised',
                        'borrowing', 'repayment', 'dividend', 'equity'
                    ],
                    'examples': as3.get('financing_examples', [])
                }
            }
    
    # Add journaling section
    tds_engine = new_data['sections'].get('tds_tcs_engine', {})
    if tds_engine and isinstance(tds_engine, dict):
        tds_sections = tds_engine.get('tds_sections', {})
        journal_templates = {}
        
        if isinstance(tds_sections, dict):
            for section_key, section_data in tds_sections.items():
                if isinstance(section_data, dict) and 'journal' in section_data:
                    section_num = section_key.replace('section_', '').upper()
                    journal_templates[f'tds_{section_num.lower()}'] = {
                        'section': section_num,
                        'template': section_data['journal'],
                        'description': section_data.get('name', '')
                    }
        
        new_data['sections']['journaling'] = {
            'meta': {
                'description': 'Journal entry templates for TDS, GST, and generic transactions',
                'usage': ['auto_journal_entries', 'journal_suggestions']
            },
            'templates': journal_templates,
            'gst_templates': {
                'rcm_purchase': {
                    'debit': ['Expense / Asset', 'Input CGST', 'Input SGST'],
                    'credit': ['RCM Output Liability'],
                    'description': 'RCM purchase entry'
                },
                'itc_availment': {
                    'debit': ['Input CGST/SGST/IGST'],
                    'credit': ['RCM Output Liability'],
                    'description': 'ITC availment entry'
                }
            }
        }
    
    # Add bank_reco section
    new_data['sections']['bank_reco'] = {
        'meta': {
            'description': 'Bank reconciliation fuzzy matching rules and parameters',
            'usage': ['bank_reconciliation', 'statement_matching']
        },
        'fuzzy_threshold': 0.6,
        'amount_tolerance': 10,
        'date_tolerance_days': 3,
        'aliases': {
            'neft': ['neft-cr', 'neft credit', 'neft from', 'neft/rtgs'],
            'cheque': ['chq', 'cheque', 'chk', 'cheque no'],
            'rtgs': ['rtgs', 'rtgs credit', 'rtgs-cr'],
            'imps': ['imps', 'imps credit', 'imps-cr'],
            'upi': ['upi', 'upi payment', 'upi credit']
        },
        'matching_rules': {
            'enable_sign_reversal': True,
            'enable_partial_match': True,
            'require_reference_match': False
        }
    }
    
    # Add generic_expansion section
    new_data['sections']['generic_expansion'] = {
        'meta': {
            'description': 'Generic rule expansion mappings for cross-engine rule usage',
            'usage': ['rule_expansion', 'logic_tree_generation']
        },
        'rule_types': {
            'schedule3': {
                'uses': 'schedule_iii_engine.schedule_iii_mapping_rules',
                'description': 'Schedule III classification rules'
            },
            'tds': {
                'uses': 'tds_tcs_engine.tds_sections',
                'description': 'TDS section classification and rates'
            },
            'gst': {
                'uses': 'gst_itc_engine.general_itc_principles',
                'description': 'GST ITC eligibility rules'
            },
            'cashflow': {
                'uses': 'cashflow',
                'description': 'Cash flow classification rules'
            },
            'journaling': {
                'uses': 'journaling.templates',
                'description': 'Journal entry templates'
            }
        }
    }
    
    # Write refactored YAML
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(new_data, f, default_flow_style=False, allow_unicode=True, 
                 sort_keys=False, width=120, indent=2)
    
    print(f"✓ Complete refactored rulebook written to: {output_file}")
    print(f"✓ Sections count: {len(new_data['sections'])}")
    print(f"✓ Sections: {list(new_data['sections'].keys())}")
    
    return True

if __name__ == '__main__':
    complete_refactor('complete_ca_rulebook_v2.yaml', 'complete_ca_rulebook_v2_canonical.yaml')
    sys.exit(0)

