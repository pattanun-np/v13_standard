# 13.0.1.0
# feature
# res.company #
# add company field require for thai accounting report
# add company address function (don't use yet)
# res.partner #
# add partner field for branch no and case customer no vat
# account.account #
# add field to support wht, wht_income,sale_tax_report,purchase_tax_report,cheque, bank_fee(don't use)
# account.cheque #
# add function to create receipt check and payment cheque from payment
# add function to post, cancel, set_to_draft, validate, reject
# add function to post from payment including cheque creation
# account.journal
# add journal property for adjust for tax
# add journal property for adjust for bank and cheque, bank revese for cheque
# add journal property for debit sequence, cn already exist
# add journal property for tax_invoice sequence - one by one invoice to tax invoice
# add journal property for payment sequence both one by one and many to one, should be RV if they gen receipt on invoice, if receipt here then keep RE
############# billing sequence #########
# account.move
# add field function for invoice and tax invoice process, adjust_move_id
# add field function for invoice and tax invoice process
# add field function for payment with cheque to have detail on account move
# add field function for supplier manual info ************* Does not use much
# add function action_invoice_generate_tax_invoice()
# add function create_reverse_tax()
# add function roundup()
# add model for account.wht.type
# inherit model for account.move.line for wht_tax,wht_type, wht_reference, amount_before_tax,invoice_date,is_debit with get_is_debit_credit()
# add function for account.move.line roundup(), roundupto()
# account.payment #
# add field for payment, write off account, cheque payment
# add function for cancel
# account.tax #
# add field for wht and tax default property,
# customer.billing #
# for customer billing and process register tax invoice with multiple invoice in one and also process receipt payment from billing
#-----------------------------------------------------------
# 13.0.1.1
# clean view file and remove un-use file
# clean models file and remove un-use file
#-----------------------------------------------------------
# 13.0.1.2
# fix generate or reverse tax for invoice and bill with "generate tax/reverse tax" button
# 13.0.1.3
# add invoice multiple register with deduction, invoice and cn can be register together
# 13.0.1.4
# change cheque validate sequence number from issue_date to validate_date
------------------------------------------------------
# 13.0.1.5
# almost sequence for multi company
#DONE

#Pending Task, Recheck function after CN same with invoice
22/03/2018 - แก้ไขการทำใบวางบิลให้รวมรายการลดหนี้ไปด้วย
09/04/2018 - แก้ไขให้ระบบไม่สามารถยกเลิกหรือลบ Customer billing ได้ถ้าไม่ใช่ "draft" หรือ "cancel"
29/04/2018 - แก้ไขการกด "Register Payment" จากหน้า Customer Billing โดยจะขึ้นเตือนหาก Invoice นั้นถูก Paid ไปแล้ว
29/04/2018 - แก้ไขให้ Customer Billing เปลี่ยนสถานะเป็น Paid หาก Invoice ถูก paid ไปแล้ว
29/04/2018 - แก้ไขให้ Refund ระบุวันที่ได้
29/04/2018 - แก้ไขการทำใบลดหนี้ เนื่องจากเหตุผลไม่ไปแสดงในเอกสารใบลดหนี้ และ วันที่ใบกำกับเก่าไม่ไปด้วย
29/04/2018 - แก้ไขให้ Check Sequence อิงจากวันที่ระบุในการ validate date
29/04/2018 - ให้การคิดหัก ณ ที่จ่ายคำนวนจำนวนเงิน จากยอดก่อน VAT และ % ได้
29/04/2018 - ตัวเลขก่อน VAT และ ตัวเลขหัก ณ ที่จ่าย เปลี่ยนจาก Monetary เป็น Float
16/06/2018 - แก้ไขเงื่อนไขในการแสดงผลของ multi-write-off ถึงแม้จะเป็น การจ่ายแบบมียอดค้างก็ให้แสดงผล Multi-write-off ไว้ด้วย


*** Well Known issue pending #######
29/04/2018 - คำนวนว่าต้องการ Write off account กรณีที่มีสกุลเงินต่างประเทศ
29/04/2018 - ผั่งรับเงิน หากสกุลเงินต่างประเทศได้เงินเกินมาจากที่ควรจะเป็นในหน้า Payment Diff จะเป็นติดลบ แต่จะลงบัญชีถูกต้อง
29/03/2018 - แก้ไขเรื่องแผนกเมื่อทำการชำระเงินแบบมี Deduction ---> change to analytic and analytic tag
16/06/2018 - remove payment_id ใน account.invoice เนื่องจากมี payment_ids ที่รวมทุก Payment มาแสดงแล้ว
********************29/04/2018 - Customer Billing, Multi Register Payment ยังมีปัญหาเรื่องการเปลี่ยนสกุลเงิน**********
##### asset how it work on V13 - by date depreciation, group by category
#### multiple check confirm, multiple check post to single gl, multiple check post to bank
#### add check from journal entry
### land cost for manufacturing
### partner manual
### customer billing for multi company
### invoice and payment in bill to
### tax report with branch, pos, invoice for POS by session.
### analytic account, tag and group how to use and apply on sales to invoice, purchase to bill, deduction
### project with boq
### analytic with budget
### tax


**** manage by itaas_print_tax_report######
29/03/2018 - แก้ไขรายงานภาษีซื้อ ให้เรียงรายการตามวันที่ใบกำกับภาษีที่ได้รับ (สรรพากรให้เรียงตามการได้มาของเอกสาร)
29/03/2018 - แก้ไขเพิ่ม Option ใน Company configuration ให้เลือกว่าจะแสดงยอมรวมในรายงานภาษีซื้อ และ ขาย ด้วยหรือไม่ (เฉพาะ Version PDF)
29/03/2018 - แก้ไขรายงานภาษีซื้อ และ ขาย ไม่ต้องแสดงเลขที่สาขา ถ้าเป็นสำนักงานใหญ่
29/03/2018 - แก้ไขรายงานภาษีซื้อ ให้รองรับการปิดภาษีประจำเดือน
29/03/2018 - แก้ไขเรื่อง รายงานภาษีขาย ทั้ง Excel และ PDF Version (จะต้องมาจาก Invoice เท่านั้น) ให้สามารถเลือกแยกระหว่างภาษีหลัก และ ภาษีอื่นๆ (แต่ภาษีอื่นจะต้องสรุปภาษีแยก) เช่น บางบริษัทมีภาษีเป็น 0 แต่กรณีที่เป็นภาษียังไม่ถึงกำหนด สุดท้ายจะอยู่ในกลุ่มภาษีหลัก
29/03/2018 - แก้ไขเรื่อง รายงานภาษีขาย ทั้ง Excel และ PDF Version (จะต้องมาจาก Invoice เท่านั้น) ให้สามารถรองรับแบบ Multi-Currency


#### apply Challet or Primus ###### not standard
29/03/2018 - แก้ไขไม่ให้แสดงปุ่ม "พิพม์ใบกำกับภาษี" แบบครั้งเดียว เนื่องจากรายงานใบกำกับของแต่ละบริษัทเป็นคนตัวกัน
29/03/2018 - เหตุผลใบลดหนี้
29/03/2018 - แก้ไขเรื่อง Credit Note ของ Supplier

——————New——by Fusion
#change unlink or cancel cheque
#change cheque new move id by validate date
#is closing month
#add tax base line amount on reverse tax for service both sale and purchase side
——————New——by Primus
#change check beginning balance and how to link original move id
#warning if gen tax without tax invoice sequence
#action gen WHT running number and account.wht.type with sequence
#add bahttext and num2words
#billing sequence by billing date
#customer_no_tax_id —>Default = False
#function to unique customer, supplier reference number —> need to remove constrain and apply Primus function instead
——————————————————————————From Primus————————————
# 13.0.1.1 Gen Seq withholding tax
# 13.0.1.2 fix check payment and assign original move to check
# 13.0.1.3 open readonly field tax_inv_number

# add function to create receipt check and payment cheque from Journal Entry
-----------
# from Onelink
# add function to post, cancel, set_to_draft, validate, reject