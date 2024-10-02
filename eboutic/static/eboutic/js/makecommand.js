/* global et_data, et_data_url, billing_info_url,
  billing_info_success_message, billing_info_failure_message */

/**
 * @readonly
 * @enum {number}
 */
const BillingInfoReqState = {
  SUCCESS: 1,
  FAILURE: 2,
  SENDING: 3
}

document.addEventListener('alpine:init', () => {
  Alpine.store('billing_inputs', {
    data: et_data,

    async fill () {
      document.getElementById('bank-submit-button').disabled = true
      const res = await fetch(et_data_url)
      if (res.ok) {
        this.data = await res.json()
        document.getElementById('bank-submit-button').disabled = false
      }
    }
  })

  Alpine.data('billing_infos', () => ({
    /** @type {BillingInfoReqState | null} */
    req_state: null,

    async send_form () {
      this.req_state = BillingInfoReqState.SENDING
      const form = document.getElementById('billing_info_form')
      document.getElementById('bank-submit-button').disabled = true
      const payload = Object.fromEntries(
        Array.from(form.querySelectorAll('input, select'))
          .filter((elem) => elem.type !== 'submit' && elem.value)
          .map((elem) => [elem.name, elem.value])
      )
      const res = await fetch(billing_info_url, {
        method: 'PUT',
        body: JSON.stringify(payload)
      })
      this.req_state = res.ok
        ? BillingInfoReqState.SUCCESS
        : BillingInfoReqState.FAILURE
      if (res.status === 422) {
        const errors = (await res.json()).detail.map((err) => err.loc).flat()
        Array.from(form.querySelectorAll('input'))
          .filter((elem) => errors.includes(elem.name))
          .forEach((elem) => {
            elem.setCustomValidity(gettext('Incorrect value'))
            elem.reportValidity()
            elem.oninput = () => elem.setCustomValidity('')
          })
      } else if (res.ok) {
        Alpine.store('billing_inputs').fill()
      }
    },

    get_alert_color () {
      if (this.req_state === BillingInfoReqState.SUCCESS) {
        return 'green'
      }
      if (this.req_state === BillingInfoReqState.FAILURE) {
        return 'red'
      }
      return ''
    },

    get_alert_message () {
      if (this.req_state === BillingInfoReqState.SUCCESS) {
        return billing_info_success_message
      }
      if (this.req_state === BillingInfoReqState.FAILURE) {
        return billing_info_failure_message
      }
      return ''
    }
  }))
})
